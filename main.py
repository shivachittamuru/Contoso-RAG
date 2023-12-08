import os
import asyncio
from typing import Any, Dict, List, Optional, Tuple, Union

import uvicorn
from fastapi import FastAPI, Body,HTTPException, Request
from fastapi.responses import StreamingResponse
from queue import Queue
# from pydantic.v1 import BaseModel as BaseModel_FastAPI
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from langchain.agents import AgentType, initialize_agent

from langchain.memory import ConversationBufferWindowMemory
from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler
from langchain.callbacks.streaming_stdout_final_only import FinalStreamingStdOutCallbackHandler
from langchain.schema import LLMResult
from langchain.chat_models import AzureChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.azuresearch import AzureSearch
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain.schema.messages import SystemMessage
from langchain.prompts import MessagesPlaceholder
from langchain.schema.agent import AgentFinish
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.memory import ConversationBufferMemory
from langchain.agents.openai_functions_agent.agent_token_buffer_memory import AgentTokenBufferMemory 
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from langchain.schema.runnable import RunnablePassthrough
from langchain.agents import AgentExecutor

import openai
import requests
from typing import AsyncGenerator
from starlette.middleware.base import BaseHTTPMiddleware

from langchain.tools import tool
from langchain.tools.convert_to_openai import format_tool_to_openai_function  
from langchain.prompts import ChatPromptTemplate
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser


from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        api_key = request.headers.get('X-API-Key')
        if api_key != "alterxrocks":
            raise HTTPException(status_code=400, detail='Invalid API Key')
        response = await call_next(request)
        return response
    
openai.api_key = os.environ['OPENAI_API_KEY']
openai.api_base = os.environ['OPENAI_API_BASE']
openai.api_type = os.environ['OPENAI_API_TYPE']
openai.api_version = os.environ['OPENAI_API_VERSION']
    
class Settings(BaseSettings):
    openai_api_type: str = os.environ['OPENAI_API_TYPE']
    openai_api_base: str= os.environ['OPENAI_API_BASE']
    openai_api_key: str = os.environ['OPENAI_API_KEY']
    openai_api_version: str = os.environ['OPENAI_API_VERSION']
    openai_model_name: str = "gpt-4"
    openai_deployment_name: str = "gpt-4"
    openai_embedding_model: str = "text-embedding-ada-002"
    azure_ai_service_endpoint: str = os.environ['AZURE_COGNITIVE_SEARCH_ENDPOINT']
    azure_ai_search_admin_key: str= os.environ['AZURE_COGNITIVE_SEARCH_KEY']
    index_name: str = "contoso-coffee-index"
    
settings = Settings()

app = FastAPI()

#app.add_middleware(APIKeyMiddleware)

embeddings: OpenAIEmbeddings = OpenAIEmbeddings(
    openai_api_type=settings.openai_api_type, 
    openai_api_base=settings.openai_api_base, 
    deployment=settings.openai_embedding_model, 
    openai_api_key=settings.openai_api_key,
    chunk_size=10, 
)

vector_store: AzureSearch = AzureSearch(
    azure_search_endpoint=settings.azure_ai_service_endpoint,
    azure_search_key=settings.azure_ai_search_admin_key,
    index_name=settings.index_name,
    embedding_function=embeddings.embed_query,
)


# initialize the tools

@tool  
def retrieve(question:str, k:int=15) -> str:  
    """
    Retrieve the top k documents from the Crypto vector store based on the user question.
    
    Parameters:  
    question (str): The user question to search the documents for.  
    k (int, optional): The number of top documents to retrieve. Default is 15.  
  
    Returns:  
    str: A string representing the context relevant to the user question, made by concatenating the page_content of the top 'k' documents. 
    """        
    docs = vector_store.hybrid_search(question, k=k)  
    context = "\n\n".join([doc.page_content for doc in docs])  
    return context  

class OrderedItem(BaseModel):
    """
    Information about each ordered item such as item name, quantity, price and additional notes provided by the customer.
    """
    item: str = Field(description="Name of the item ordered")
    quantity: int = Field(description="Quantity of that ordered item")
    price: float = Field(description="Price of that ordered item")
    item_notes: Optional[str] = Field(description="Any additional notes about that item provided by the customer")
    
class OrderInfo(BaseModel):
    """
    Input is a transcript of a conversation between a customer and an AI assistant discussing an order made at a restaurant.
    Extract order details such item name, quantity, price, and any additional notes for each item.
    """
    order: List[OrderedItem] = Field(description="List of items ordered and their details")

@tool(args_schema=OrderInfo)  
def calculate_total(order: list) -> str:  
    """
    Calculate the total price of the order.
    
    Parameters:  
    order (list): A list of dictionaries, where each dictionary represents an item in the order and  has 'price' and 'quantity' keys.  
  
    Returns:  
    str: A string representing the total price of the order. 
    """  
    sum = 0
    for item in order:
        sum += item['price']*item['quantity']
    return f"The total price of the order excluding tax is ${sum}"

tool_list = [retrieve, calculate_total]
functions = [format_tool_to_openai_function(f) for f in tool_list]

# initialize the agent (we need to do this for the callbacks)
model = AzureChatOpenAI(   
    openai_api_key=settings.openai_api_key,
    openai_api_type=settings.openai_api_type,
    openai_api_base=settings.openai_api_base,
    openai_api_version=settings.openai_api_version,
    deployment_name=settings.openai_deployment_name, 
    model_name=settings.openai_model_name,   
    temperature=0.0,    
    streaming=True,  # ! important
    callbacks=[]  # ! important (but we will add them later)
)

model_with_tools = model.bind(functions=functions)
    
prompt = ChatPromptTemplate.from_messages([
    (
        "system", 
        """
            You are a Coffee Ordering assistant for Contoso Coffee cafe and have access to two tools. Menu includes coffees, teas, bakery items, sandwiches and smoothies. As an agent, your job is to receive orders from customers and answer their inquiries about the menu items. 
            
            First tool is "retrieve" function. It can retrieve context based on user question from vector store that contains information about cafe's menu items. 
            You may need this tool to obtain information about the menu items and answer questions. Feel free to skip this tool if you don't need the context to answer the question. For example, when customer is greeting or when you can find answer from conversation history. 
            
            Second tool is "calculate_total" function. Since you are not an expert in math and calculations, use this tool to calculate the total price of the order (excluding tax) based on the items ordered and their prices.
            Do not use this tool until user specifically requests for the total price of the order.                       
            
            Please follow these instructions when interacting with customers to generate a good and brief conversation:
            • Since you are representing Contoso, NEVER MENTION 'I am an AI language model'. Always respond in first person, not in third person. Focus solely on cafe-related queries and ordering. 
            • Keep responses concise and clear. Long responses may disengage the customers. Do not provide additional information, such as description, until explicitly asked for. Do not repeat anything until asked for, especially if you already mentioned in the conversation history.
            • If a customer is asking for recommendations, provide only top 3 most relevant recommendations. Do not provide more than 3 as it may lead to a long response.
            • Inform the customer politely if an item they request is not available in the listed menu items below. If a customer likes to update or cancel the order, please help accordingly.
            • Capture any additional notes the customer may have for the menu items.
            • When listing an item in the order, mention the actual price of the item in parenthesis without multiplying it with the quantity.
            • At the end of each conversation, always obtain the customer's name, even if provided in a single word, and attach it to the order.
            • Once the customer provides their name, confirm it and state that the order can be picked up at our cafe in 15 minutes.
            • Contoso accepts only pickup orders. Payment is accepted only at the store, and if a customer suggests paying over the phone, inform them that payments are accepted solely at the store.
        Remember to always maintain a polite and professional tone.
        
        Conversaion History:
        {chat_history}
        """
                 
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "User Input: {input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

chain = prompt | model_with_tools | OpenAIFunctionsAgentOutputParser()

agent_chain = RunnablePassthrough.assign(
    agent_scratchpad= lambda x: format_to_openai_functions(x["intermediate_steps"])
) | chain

memory = ConversationBufferMemory(return_messages=True,memory_key="chat_history")

agent_executor = AgentExecutor(agent=agent_chain, tools=tool_list, verbose=False, memory=memory)

class UserQuery(BaseModel):
    """
    user and session related things
    """
    text: str
    user_id:str
    
    
async def generate_response(
        message: str,
) -> AsyncGenerator[str,None]:
    response=""
    async for token in agent_executor.astream({"input": message}):
        if('output' in token.keys()):
            print(token["output"])
            yield token["output"]
            response += token["output"]
            
            
@app.post("/chat/stream")
async def chat(
    query: UserQuery = Body(...),
): 
    return StreamingResponse(generate_response(query.text), media_type="text/event-stream")


@app.post("/chat/v1")
async def chat(
    query: UserQuery = Body(...),
): 
    result = agent_executor.invoke({"input": query.text}) 
    return result['output'].replace('"', '')


@app.get("/health")
async def health():
    """Check the api is running"""
    return {"status": "🤙"}

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="localhost",
        port=8000,
        reload=True,
        env_file=".env"
    )