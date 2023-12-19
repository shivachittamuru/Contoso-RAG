
import os
import openai
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic.v1 import BaseModel, Field

from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.azuresearch import AzureSearch
from langchain.tools import tool
from langchain.tools.convert_to_openai import format_tool_to_openai_function  

from settings import app_settings as settings

embeddings: OpenAIEmbeddings = OpenAIEmbeddings(model=settings.embedding_model, chunk_size=10)

vector_store: AzureSearch = AzureSearch(
    azure_search_endpoint=settings.azure_ai_service_endpoint,
    azure_search_key=settings.azure_ai_search_admin_key,
    index_name=settings.ai_search_index_name,
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