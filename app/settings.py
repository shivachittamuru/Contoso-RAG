# Settings file to centralize all the configuration settings for the application
# Change settings here to change the behavior of the application without modifying the code


import os
from pydantic_settings import BaseSettings

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

class AppSettings(BaseSettings):
    openai_api_type: str = os.environ.get('OPENAI_API_TYPE')
    openai_api_base: str = os.environ.get('OPENAI_API_BASE')
    openai_api_key: str = os.environ.get('OPENAI_API_KEY')
    openai_api_version: str = os.environ.get('OPENAI_API_VERSION')
    openai_model_name: str = os.environ.get('CHAT_MODEL_NAME')
    openai_deployment_name: str = os.environ.get('CHAT_MODEL_NAME')
    embedding_model: str = os.environ.get('EMBEDDING_MODEL_NAME')
    azure_ai_service_endpoint: str = os.environ.get('AZURE_COGNITIVE_SEARCH_ENDPOINT')
    azure_ai_search_admin_key: str = os.environ.get('AZURE_COGNITIVE_SEARCH_KEY')
    ai_search_index_name: str = os.environ.get('AZURE_COGNITIVE_SEARCH_INDEX_NAME')
    cosmos_endpoint: str = os.environ.get('AZURE_COSMOSDB_ENDPOINT')
    cosmos_key: str = os.environ.get('AZURE_COSMOSDB_KEY')
    cosmos_database_name: str = os.environ.get('AZURE_COSMOSDB_NAME')
    cosmos_container_name: str = os.environ.get('AZURE_COSMOSDB_CONTAINER_NAME')
    cosmos_connection_string: str = os.environ.get('AZURE_COMOSDB_CONNECTION_STRING')
    azure_b2c_expected_issuer: str = os.environ.get('AZURE_B2C_EXPECTED_ISSUER')
    azure_b2c_jwks_uri: str = os.environ.get('AZURE_B2C_JWKS_URI')
    azure_b2c_audience: str = os.environ.get('AZURE_B2C_AUDIENCE')

    class Config:
        env_file = ".env"

app_settings = AppSettings()

