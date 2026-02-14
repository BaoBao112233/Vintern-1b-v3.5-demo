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
from app.api.cameras import router as cameras_router
from app.api.inference import router as inference_router
from app.services.local_model import get_local_model
from app.services.object_detection import get_object_detector
from app.services.local_runner import LocalRunner
from app.services.websocket_manager import WebSocketManager
from app.services.camera_manager import get_camera_manager, initialize_cameras
from app.services.detection_client import get_detection_client
from app.services.vllm_client import initialize_vllm_client

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
camera_manager = None
detection_client = None
vllm_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup and cleanup on shutdown"""
    global hf_client, local_runner, local_model, object_detector, websocket_manager, camera_manager, detection_client, vllm_client
    
    logger.info("Starting Vintern-1B Realtime Demo Backend...")
    
    # Initialize WebSocket manager
    websocket_manager = WebSocketManager()
    
    # Initialize VLLM client (Orange Pi service)
    logger.info("Initializing VLLM client...")
    try:
        vllm_client = await initialize_vllm_client()
        if vllm_client.is_available():
            logger.info("✅ VLLM client connected to Orange Pi")
        else:
            logger.warning("⚠️  VLLM client not available (detection only mode)")
    except Exception as e:
        logger.error(f"Failed to initialize VLLM client: {e}")
        logger.warning("Continuing without VLLM service")
    
    # Initialize detection client
    logger.info("Initializing detection client...")
    detection_client = await get_detection_client()
    
    # Initialize camera manager
    logger.info("Initializing cameras...")
    try:
        camera_manager = await initialize_cameras()
        logger.info("✅ Cameras initialized")
    except Exception as e:
        logger.error(f"Failed to initialize cameras: {e}")
    
    # Always initialize object detector (keep for backward compatibility)
    logger.info("Initializing object detector...")
    object_detector = await get_object_detector()
    
    # Initialize model services based on mode (optional for camera-only detection)
    model_mode = os.getenv("MODEL_MODE", "none").lower()  # Default to 'none' for camera detection only
    logger.info(f"Model mode: {model_mode}")
    
    if model_mode == "hf":
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            logger.warning("HF_TOKEN not found. Remote inference may not work.")
        hf_client = HuggingFaceClient(token=hf_token)
        await hf_client.initialize()
    elif model_mode == "local":
        logger.info("Initializing local model...")
        try:
            local_model = await get_local_model()
            
            # Fallback to local_runner if needed
            if not local_model.is_available():
                logger.warning("Local model not available, trying LocalRunner...")
                model_path = os.getenv("LOCAL_MODEL_PATH", "/models")
                local_runner = LocalRunner(model_path=model_path)
                await local_runner.initialize()
        except Exception as e:
            logger.warning(f"Failed to initialize local model: {e}")
            logger.info("Continuing without VLM model (camera detection only)")
    else:
        logger.info("Running in camera detection mode only (no VLM model)")
    
    logger.info("Backend initialized successfully!")
    
    yield
    
    # Cleanup
    logger.info("Shutting down backend...")
    if hf_client:
        await hf_client.cleanup()
    if local_model:
        await local_model.cleanup()
    if local_runner:
        await local_runner.cleanup()
    if websocket_manager:
        await websocket_manager.cleanup()
    if camera_manager:
        camera_manager.stop_all()
    if detection_client:
        await detection_client.cleanup()
    if vllm_client:
        await vllm_client.cleanup()

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
    allow_origins=["*"],  # Allow all origins for camera access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(cameras_router, prefix="/api", tags=["cameras"])
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(predict_router, prefix="/api", tags=["predict"])
app.include_router(inference_router, prefix="/api", tags=["inference"])

# Mount static files for frontend UI
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    logger.info(f"✅ Mounted static files from {static_dir}")
    
    # Serve index.html at root
    @app.get("/ui")
    async def serve_ui():
        """Serve frontend UI"""
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"error": "UI not built yet"}

    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {en-1B Realtime Demo API",
        "status": "runnin
        "version": "1.0.0",
        "endpoints": {
            "ui": "/ui",
            "api_docs": "/docs",
            "health": "/api/health"
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    model_mode = os.getenv("MODEL_MODE", "local").lower()
    
    status = {
        "status": "healthy",
        "model_mode": model_mode,
        "model_ready": False,
        "object_detection_ready": False,
        "detection_service_ready": False,
        "cameras_ready": False,
        "vllm_ready": False
    }
    
    # Check VLLM client
    if vllm_client:
        status["vllm_ready"] = vllm_client.is_available()
        if status["vllm_ready"]:
            status["vllm_info"] = vllm_client.get_info()
    
    # Check detection client
    if detection_client:
        status["detection_service_ready"] = detection_client.is_ready()
    
    # Check camera manager
    if camera_manager:
        camera_status = camera_manager.get_status()
        status["cameras_ready"] = len(camera_status) > 0
        status["cameras"] = camera_status
    
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