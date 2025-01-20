from fastapi import FastAPI
import os
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from pydantic import BaseModel
from chatbot import Chatbot  # Make sure this imports your Chatbot class

from pathlib import Path
import logging
from contextlib import asynccontextmanager
logging.basicConfig(level=logging.INFO)

# Define UserInput model for request body
class UserInput(BaseModel):
    query: str
    thread_id: str = "1"  # Default thread ID for session tracking

app = FastAPI()

# Use lifespan event handler instead of on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("FastAPI App Started")
    yield  # This allows the app to start serving requests
    logging.info("FastAPI App Shutting Down")

app = FastAPI(lifespan=lifespan)

# # Absolute paths to your directories
# BASE_DIR = "D:/fastapi-project"  # Change this to the correct absolute path
# STATIC_DIR = os.path.join(BASE_DIR, "static")
# TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Serve static files
app.mount("/static", StaticFiles(directory= "static"), name="static")

# Set up Jinja2 template rendering
templates = Jinja2Templates(directory= "templates")

# Create an instance of the Chatbot
chatbot = Chatbot()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    logging.info("Serving index.html")
    return templates.TemplateResponse("index.html", {"request": request})

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"Request path: {request.url.path}")
    response = await call_next(request)
    return response

@app.post("/query")
async def query_chatbot(user_input: UserInput):
    response = chatbot.invoke_graph(user_input.query)
    return {"response": response}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Use the PORT variable, default to 8000 if not set

    # Print the port number before starting the server
    print(f"Starting on port {port}")

    uvicorn.run("app:app", host="0.0.0.0", port=port)
