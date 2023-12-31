   
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine
from routers import auth, agent, users, static
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

import os
from settings import app_settings as settings
from contextlib import asynccontextmanager
from langchain.chat_models import AzureChatOpenAI


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the Settings and TOols 

    ## langsmith configuration
    os.environ["LANGCHAIN_TRACING_V2"]="true"
    os.environ["LANGCHAIN_ENDPOINT"]="https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"]="ls__dd5ee908c54e46e0ab05fedfc824a7c8"
    os.environ["LANGCHAIN_PROJECT"]="alterx-ai-alpha"

    # lang_smith_client = LangsmithClient()
    # url = next(lang_smith_client.list_runs(project_name="alterx-ai-alpha")).url
    # print(url)

    openai_chat_client = AzureChatOpenAI(
        temperature=0.0,
        max_tokens=500,
        openai_api_key=settings.openai_api_key,  
        openai_api_version=settings.openai_api_version,
        openai_api_type=settings.openai_api_type,
        openai_api_base=settings.openai_api_base,   
        deployment_name=settings.openai_deployment_name,   
        streaming=True,   
        callbacks=[]         
    ) 
    
    app.state.azure_openai_chat_client = openai_chat_client
    
    # db = get_db()
    # app.state.settings.db = db

    print("I am in the startup of the app!!")

    # Anything after this will be called on shutdown for cleanup activity
    yield
     # Clean up the ML models and release the resources   
    openai_chat_client.close()  
    # db.close()

app = FastAPI(lifespan=lifespan)

build_path = '../frontend/cafe/dist'    
# Serve the static files from the React app's build directory
app.mount("/app", StaticFiles(directory=build_path, html=True), name="static")

@app.get("/health")
async def health():
    """Check the api is running"""
    return {"status": "🤙"}

@app.get("/")
async def root():
    return RedirectResponse(url='/app/')

models.Base.metadata.create_all(engine)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(agent.router)
# app.include_router(static.router)

# Add SessionMiddleware with your secret key
app.add_middleware(SessionMiddleware, secret_key="contosokey")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)

