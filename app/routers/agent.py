
# from pydantic.v1 import BaseModel, Field
# from pydantic import BaseModel as BaseModel_FastAPI

from langchain.chat_models import AzureChatOpenAI
from langchain.prompts import MessagesPlaceholder
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.schema.runnable import RunnablePassthrough
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents import AgentExecutor
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.memory import CosmosDBChatMessageHistory

from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import Body, Request, APIRouter, Depends, HTTPException
from starlette import status
# from starlette.requests import Request
from tools import tool_list, functions
import random
from prompts import CHAIN_SYSTEM_PROMPT, AGENT_SYSTEM_PROMPT
from models import User
from database import get_db
from .auth import db_dependency, get_current_user, verify_password, get_password_hash, credentials_exception
from settings import app_settings as settings

from uuid import UUID

# from langsmith import Client
# client = Client()
# os.environ['LANGCHAIN_PROJECT'] = "contoso-agent"


router = APIRouter(
    prefix="/agent",
    tags=["agent"]
)

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

async def get_agent(user: dict, request: Request) -> AgentExecutor:    
    user_id = user['id']
    user_name = user['username']
    
    if 'session_id' not in request.session:  
        request.session['session_id'] = "Session" + str(random.randint(1, 10000))            
    # print(user_id)  
    # print(user_name)
    # print(request.session['session_id'])
    
    # model = AzureChatOpenAI(temperature=0.0,
    #     max_tokens=400,
    #     openai_api_base=settings.openai_api_base,
    #     openai_api_version=settings.openai_api_version,
    #     deployment_name=settings.openai_deployment_name,
    #     openai_api_key=settings.openai_api_key,
    #     openai_api_type = settings.openai_api_type,
    #     streaming=False,
    # )
    
    model = request.app.state.azure_openai_chat_client
    
    # Create CosmosDB instance from langchain cosmos class.
    cosmos = CosmosDBChatMessageHistory(
            cosmos_endpoint=settings.cosmos_endpoint,
            cosmos_database=settings.cosmos_database_name,
            cosmos_container=settings.cosmos_container_name,
            connection_string=settings.cosmos_connection_string,
            session_id=request.session['session_id'],  # Use the session ID from the session  
            user_id=str(user_id) 
        )
    cosmos.prepare_cosmos()

    model_with_tools = model.bind(functions=functions)
    
    agent_prompt = AGENT_SYSTEM_PROMPT + "User Name: {0}\n".format(user_name)
    print(user_name)

    prompt = ChatPromptTemplate.from_messages([
        ("system", agent_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "User Input: {input} \n Answer:"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])

    chain = prompt | model_with_tools | OpenAIFunctionsAgentOutputParser()
    agent_chain = RunnablePassthrough.assign(
        agent_scratchpad= lambda x: format_to_openai_functions(x["intermediate_steps"])
    ) | chain
    
    # memory = ConversationBufferMemory(return_messages=True,memory_key="chat_history")
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, chat_memory=cosmos)

    agent_executor = AgentExecutor(agent=agent_chain, tools=tool_list, verbose=False, memory=memory)    
    return agent_executor

######################
# Agent Streaming Handler

from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler
from typing import Any
from langchain.schema import LLMResult
import asyncio
from fastapi.responses import StreamingResponse

class AsyncCallbackHandler(AsyncIteratorCallbackHandler):   
    def __init__(self) -> None:
        super().__init__()

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:  
        print(token)             
        self.queue.put_nowait(token)   
    
    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:        
        if response.generations[0][0].generation_info['finish_reason'] == 'stop':    
            self.done.set()       

async def run_call(query: str, stream_it: AsyncCallbackHandler, user: user_dependency, request: Request):
    # assign callback handler
    request.app.state.azure_openai_chat_client.callbacks = [stream_it]
    agent = await get_agent(user, request)
    # now query
    await agent.acall(inputs={"input": query})

async def create_gen(query: str, 
                     stream_it: AsyncCallbackHandler,
                     user: user_dependency,                     
                     request: Request):
    task = asyncio.create_task(run_call(query, stream_it, user, request))
    async for token in stream_it.aiter():       
        yield token
    await task

######################


@router.get('/chat', status_code=status.HTTP_200_OK)
async def run_agent(
    query: str,
    db: db_dependency,
    user: user_dependency,
    request: Request
):
    """
    Chat with the agent.
    """
    db_user = db.query(User).get(user['id'])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")    
    
    agent_executor = await get_agent(user, request)        
    result = await agent_executor.ainvoke({"input": query}) 
    return result['output'].replace('"', '') 


@router.get("/chat/stream")
async def run_agent_streaming(
    query: str,
    db: db_dependency,
    user: user_dependency,
    request: Request = None
): 
    """
    Chat with the agent with streaming turned on.
    """
    db_user = db.query(User).get(user['id'])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")   
    
    stream_it = AsyncCallbackHandler()  
    gen = create_gen(query, stream_it, user, request)
    return StreamingResponse(gen, media_type="text/event-stream")    