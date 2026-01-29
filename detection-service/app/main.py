"""
Detection Service - FastAPI Application
Raspberry Pi 4 + Coral USB Accelerator
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.detect import router as detect_router
from app.models.detector import get_detector

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup"""
    logger.info("🚀 Starting Detection Service...")
    logger.info(f"📍 Service IP: {os.getenv('SERVICE_IP', '192.168.100.10')}")
    
    # Initialize detector
    detector = await get_detector()
    
    if detector.is_ready():
        logger.info("✅ Detection Service ready!")
    else:
        logger.error("❌ Detector failed to initialize")
    
    yield
    
    logger.info("👋 Shutting down Detection Service...")


# Create app
app = FastAPI(
    title="Detection Service",
    description="Object Detection using Coral TPU on Raspberry Pi 4",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(detect_router, prefix="/api", tags=["detection"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Detection Service",
        "status": "running",
        "hardware": "Raspberry Pi 4 + Coral USB",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check"""
    detector = await get_detector()
    
    return {
        "status": "healthy",
        "detector_ready": detector.is_ready() if detector else False,
        "service_ip": os.getenv("SERVICE_IP", "192.168.100.10"),
        "vllm_service": os.getenv("VLLM_SERVICE_URL", "http://192.168.100.20:8002")
    }


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """WebSocket for real-time detection streaming"""
    await websocket.accept()
    logger.info("WebSocket client connected")
    
    try:
        detector = await get_detector()
        
        while True:
            # Receive base64 image
            data = await websocket.receive_json()
            
            if not detector.is_ready():
                await websocket.send_json({
                    "error": "Detector not ready"
                })
                continue
            
            # Process detection
            try:
                import base64
                import io
                import numpy as np
                from PIL import Image
                import cv2
                
                image_bytes = base64.b64decode(data.get('image', ''))
                image = Image.open(io.BytesIO(image_bytes))
                image_np = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                
                detections = await detector.detect(image_np)
                summary = detector.get_summary(detections)
                
                await websocket.send_json({
                    "success": True,
                    "detections": detections,
                    "summary": summary
                })
                
            except Exception as e:
                logger.error(f"Detection error: {e}")
                await websocket.send_json({
                    "error": str(e)
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
