
# from pydantic.v1 import BaseModel, Field
# from pydantic import BaseModel as BaseModel_FastAPI

import json
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
from fastapi import Body, Request, APIRouter, Depends, HTTPException, WebSocket
from starlette import status
from starlette.websockets import WebSocketDisconnect
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

async def get_agent_websocket(user: dict, model: AzureChatOpenAI) -> AgentExecutor:    
    user_id = user['id']
    user_name = user['username']
    
    session_id = "Session" + str(random.randint(1, 10000))

    # Create CosmosDB instance from langchain cosmos class.
    cosmos = CosmosDBChatMessageHistory(
            cosmos_endpoint=settings.cosmos_endpoint,
            cosmos_database=settings.cosmos_database_name,
            cosmos_container=settings.cosmos_container_name,
            connection_string=settings.cosmos_connection_string,
            session_id=session_id,  # Use the session ID from the session  
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
    
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, chat_memory=cosmos)

    agent_executor = AgentExecutor(agent=agent_chain, tools=tool_list, verbose=False, memory=memory)    
    return agent_executor

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
        print('inside on_llm_end')      
        if response.generations[0][0].generation_info['finish_reason'] == 'stop':    
            print('inside on_llm_end -  stop')
            self.done.set()       

class AsyncWebsocketCallbackHandler(AsyncIteratorCallbackHandler):   
    def __init__(self, websocket: WebSocket) -> None:
        super().__init__()
        self.websocket = websocket

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:  
        print(token)
        await self.websocket.send_text(json.dumps({"message": token, "end_of_message": False}))             
        self.queue.put_nowait(token)   
    
    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:  
        print('inside on_llm_end')      
        if response.generations[0][0].generation_info['finish_reason'] == 'stop':    
            print('inside on_llm_end -  stop')
            await self.websocket.send_text(json.dumps({"message": "", "end_of_message": True}))
            self.done.set()

async def run_call(query: str, stream_it: AsyncCallbackHandler, user: user_dependency, request: Request):
    # assign callback handler
    request.app.state.azure_openai_chat_client.callbacks = [stream_it]
    agent = await get_agent(user, request)
    # now query
    await agent.acall(inputs={"input": query})

async def run_websocket_call(query: str, stream_it: AsyncWebsocketCallbackHandler, user: user_dependency, model: AzureChatOpenAI):
    # assign callback handler
    model.callbacks = [stream_it]
    print('inside run_websocket_call and the model callbacks are set')
    agent = await get_agent_websocket(user, model)
    print('inside run_websocket_call and the agent is set')
    # now query
    await agent.acall(inputs={"input": query})

async def create_gen(query: str, 
                     stream_it: AsyncCallbackHandler,
                     user: user_dependency,                     
                     request: Request):
    task = asyncio.create_task(run_call(query, stream_it, user, request))
    
    try:
        async for token in stream_it.aiter():
            print('inside stream_it.aiter() about to yield a token')
            yield token
            # Optionally, you could check if task is done and break if needed:
            if task.done():
                break
    except Exception as e:
        # Properly handle exceptions, possibly logging them
        logger.error(f"Error in stream generator: {e}")
        task.cancel()  # Cancel the background task if the stream_it iteration fails
        raise
    finally:
        # Wait for the task to ensure it gets cleaned up properly
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

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, token: str):
    try:
        print('inside websocket_chat')
        print(f'token: ${token}')
        user = await validate_user_token(token)  
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")

        print('user validated')
        await websocket.accept()
        print('websocket accepted')
        
        await websocket.send_text(json.dumps({"message": "Welcome to the chat!"}))

        model = websocket.app.state.azure_openai_chat_client
        
        stream_it = AsyncWebsocketCallbackHandler(websocket)
        task = asyncio.create_task(run_websocket_call(websocket, stream_it, user, model))
        
        print('task created')
        try:
            while True:
                print('inside while loop')
                data = await websocket.receive_text()
                print(f"While Loop Received data: {data}")
                await process_streaming_request(data, stream_it, user, model, websocket)
                print('processed streaming request')
                async for message in stream_it.aiter():
                    print('inside stream_it.aiter() about to send a message')
                    print(f"Sending message: {message}")
                    await websocket.send_text(message)
                    print('message sent')
        except WebSocketDisconnect:
            print("WebSocket disconnected")
        finally:
            task.cancel()

    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()

async def process_streaming_request(data, stream_it, user, model: AzureChatOpenAI, websocket: WebSocket):
    # Extract the query from the received data
    query = data  # Modify this line if data format is different
    # Start processing the query
    await run_websocket_call(query, stream_it, user, model)
    # You may need to adjust this based on how your agent is set up

async def validate_user_token(token: str):
    return {'username': 'bobjac', 'id': 3, 'role': 'admin'}