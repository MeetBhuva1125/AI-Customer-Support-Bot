from dotenv import load_dotenv

# Load environment variables FIRST before any other imports
load_dotenv(override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from app.database import init_db
from app.routes import chat, session

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting AI Customer Support Bot...")
    print(f"✓ Environment loaded from .env")
    print(f"✓ API Key present: {bool(os.getenv('GEMINI_API_KEY'))}")
    
    await init_db()
    yield
    # Shutdown
    print("👋 Shutting down...")

app = FastAPI(
    title="AI Customer Support Bot",
    description="Intelligent customer support chatbot with FAQ matching and escalation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(session.router)

# Serve frontend static files
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def root():
    return {
        "message": "AI Customer Support Bot API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "chat_ui": "/chat-ui",
            "create_session": "POST /session/new",
            "chat": "POST /chat",
            "get_history": "GET /chat/history/{session_id}",
            "get_session": "GET /session/{session_id}",
            "close_session": "DELETE /session/{session_id}"
        }
    }

@app.get("/chat-ui")
async def serve_chat_ui():
    """Serve the chat interface"""
    return FileResponse("frontend/index.html")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "gemini_api_configured": bool(os.getenv("GEMINI_API_KEY"))
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
