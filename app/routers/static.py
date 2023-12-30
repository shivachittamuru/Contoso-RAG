from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# router = APIRouter()
router = FastAPI()

# Path to the directory where your Vite React app's build files are located
build_path = '/Users/bobjacobs/work/src/github.com/shivachittamuru/Contoso-RAG/frontend/cafe/dist'

# Serve the static files from the React app's build directory
router.mount("/static", StaticFiles(directory=build_path, html=True), name="static")
