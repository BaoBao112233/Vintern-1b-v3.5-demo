"""
Vintern Vision AI Backend
FastAPI server with RTSP → Detection → VLM pipeline
"""

import os
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.services.pipeline import VisionPipeline

# Load environment
load_dotenv()

# Logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global pipeline instance
pipeline: Optional[VisionPipeline] = None

# WebSocket connections
ws_connections = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global pipeline
    
    logger.info("🚀 Starting Vintern Vision AI Backend")
    logger.info("=" * 70)
    
    # Get configuration
    camera_urls = {
        'camera1': os.getenv('CAMERA_1_URL'),
        'camera2': os.getenv('CAMERA_2_URL')
    }
    
    vllm_url = os.getenv('VLLM_API_URL', 'http://localhost:8000/v1')
    detection_conf = float(os.getenv('DETECTION_CONF_THRESHOLD', '0.5'))
    sample_rate = float(os.getenv('FRAME_SAMPLE_RATE', '1.0'))
    
    # Validate configuration
    if not all(camera_urls.values()):
        logger.error("❌ Camera URLs not configured in .env")
        raise RuntimeError("Missing camera configuration")
    
    logger.info("📋 Configuration:")
    logger.info(f"   Cameras: {list(camera_urls.keys())}")
    logger.info(f"   vLLM API: {vllm_url}")
    logger.info(f"   Detection confidence: {detection_conf}")
    logger.info(f"   Sample rate: {sample_rate} FPS")
    
    # Initialize pipeline
    try:
        pipeline = VisionPipeline(
            camera_urls=camera_urls,
            vllm_api_url=vllm_url,
            detection_conf=detection_conf,
            sample_rate=sample_rate
        )
        
        pipeline.initialize()
        pipeline.start()
        
        logger.info("✅ Pipeline started successfully")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Failed to start pipeline: {e}")
        raise
    
    # Run
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down...")
    
    if pipeline:
        pipeline.stop()
    
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Vintern Vision AI",
    description="Real-time vision AI pipeline with RTSP cameras",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# REST API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Vintern Vision AI",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    stats = pipeline.get_stats()
    
    return {
        "status": "healthy" if stats['running'] else "degraded",
        "pipeline_running": stats['running'],
        "cameras": stats.get('camera_status', {})
    }


@app.get("/cameras")
async def get_cameras():
    """Get camera list and status"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    stats = pipeline.get_stats()
    camera_status = stats.get('camera_status', {})
    
    cameras = []
    for camera_id, status in camera_status.items():
        cameras.append({
            "id": camera_id,
            "name": camera_id.replace('_', ' ').title(),
            "connected": status.get('connected', False),
            "running": status.get('running', False),
            "frame_count": status.get('frame_count', 0)
        })
    
    return {"cameras": cameras}


@app.get("/results")
async def get_results():
    """Get latest results from all cameras"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    results = pipeline.get_latest_results()
    
    # Format results for frontend
    formatted_results = {}
    for camera_id, result in results.items():
        formatted_results[camera_id] = {
            "camera_id": camera_id,
            "timestamp": result.get('timestamp'),
            "frame_number": result.get('frame_number'),
            "detection": {
                "summary": result.get('detection_summary', 'No objects detected'),
                "boxes": result.get('detection', {}).get('boxes', []),
                "classes": result.get('detection', {}).get('class_names', []),
                "scores": result.get('detection', {}).get('scores', [])
            },
            "vlm_analysis": result.get('vlm_analysis', None)
        }
    
    return formatted_results


@app.get("/stats")
async def get_stats():
    """Get pipeline statistics"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    return pipeline.get_stats()


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    ws_connections.add(websocket)
    
    logger.info(f"🔌 WebSocket connected (total: {len(ws_connections)})")
    
    try:
        # Send initial status
        if pipeline:
            stats = pipeline.get_stats()
            await websocket.send_json({
                "type": "status",
                "data": stats
            })
        
        # Stream updates
        while True:
            if pipeline is None:
                await asyncio.sleep(1)
                continue
            
            # Get latest results
            results = pipeline.get_latest_results()
            stats = pipeline.get_stats()
            
            # Send update
            await websocket.send_json({
                "type": "update",
                "timestamp": asyncio.get_event_loop().time(),
                "results": {
                    camera_id: {
                        "detection_summary": result.get('detection_summary'),
                        "vlm_analysis": result.get('vlm_analysis'),
                        "frame_number": result.get('frame_number')
                    }
                    for camera_id, result in results.items()
                },
                "stats": {
                    "frames_received": stats.get('frames_received', 0),
                    "frames_detected": stats.get('frames_detected', 0),
                    "frames_analyzed": stats.get('frames_analyzed', 0)
                }
            })
            
            # Wait before next update
            await asyncio.sleep(1.0)
    
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket disconnected")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    finally:
        ws_connections.discard(websocket)
        logger.info(f"🔌 WebSocket removed (total: {len(ws_connections)})")


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"❌ Unhandled exception: {exc}")
    import traceback
    traceback.print_exc()
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv('BACKEND_HOST', '0.0.0.0')
    port = int(os.getenv('BACKEND_PORT', '8001'))
    
    logger.info(f"🚀 Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
