"""
Vintern-1B Realtime Camera Inference Demo - Backend
FastAPI application with WebSocket support for realtime camera inference
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.api.predict import router as predict_router
from app.api.chat import router as chat_router
from app.services.hf_client import HuggingFaceClient
from app.services.local_model import get_local_model
from app.services.object_detection import get_object_detector
from app.services.local_runner import LocalRunner
from app.services.websocket_manager import WebSocketManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for model services
hf_client = None
local_runner = None
local_model = None
object_detector = None
websocket_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup and cleanup on shutdown"""
    global hf_client, local_runner, local_model, object_detector, websocket_manager
    
    logger.info("Starting Vintern-1B Realtime Demo Backend...")
    
    # Initialize WebSocket manager
    websocket_manager = WebSocketManager()
    
    # Always initialize object detector
    logger.info("Initializing object detector...")
    object_detector = await get_object_detector()
    
    # Initialize model services based on mode
    model_mode = os.getenv("MODEL_MODE", "local").lower()  # Changed default to local
    logger.info(f"Model mode: {model_mode}")
    
    if model_mode == "hf":
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            logger.warning("HF_TOKEN not found. Remote inference may not work.")
        hf_client = HuggingFaceClient(token=hf_token)
        await hf_client.initialize()
    elif model_mode == "local":
        logger.info("Initializing local model...")
        local_model = await get_local_model()
        
        # Fallback to local_runner if needed
        if not local_model.is_available():
            logger.warning("Local model not available, trying LocalRunner...")
            model_path = os.getenv("LOCAL_MODEL_PATH", "/models")
            local_runner = LocalRunner(model_path=model_path)
            await local_runner.initialize()
    
    logger.info("Backend initialized successfully!")
    
    yield
    
    # Cleanup
    logger.info("Shutting down backend...")
    if hf_client:
        await hf_client.cleanup()
    if local_runner:
        await local_runner.cleanup()
    if websocket_manager:
        await websocket_manager.cleanup()

# Create FastAPI app
app = FastAPI(
    title="Vintern-1B Realtime Demo API",
    description="Realtime camera inference using 5CD-AI/Vintern-1B-v3_5 model",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(predict_router, prefix="/api")
app.include_router(chat_router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Vintern-1B Realtime Demo API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    model_mode = os.getenv("MODEL_MODE", "local").lower()
    
    status = {
        "status": "healthy",
        "model_mode": model_mode,
        "model_ready": False,
        "object_detection_ready": False
    }
    
    # Check object detection
    if object_detector:
        status["object_detection_ready"] = object_detector.is_available()
    
    # Check model
    if model_mode == "hf" and hf_client:
        status["model_ready"] = hf_client.is_ready()
        status["model_info"] = hf_client.get_model_info()
    elif model_mode == "local":
        if local_model and local_model.is_available():
            status["model_ready"] = True
            status["model_info"] = local_model.get_model_info()
        elif local_runner and local_runner.is_ready():
            status["model_ready"] = local_runner.is_ready()
            status["model_info"] = local_runner.get_model_info()
    
    return status

@app.websocket("/ws/predict")
async def websocket_predict(websocket: WebSocket):
    """WebSocket endpoint for realtime inference"""
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Receive frame data from client
            data = await websocket.receive_json()
            
            # Process frame asynchronously
            await websocket_manager.process_frame(websocket, data)
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )