#!/usr/bin/env python3
"""
Integrated Backend API for Camera + VLM + Detection
FastAPI service that combines all components
"""

import os
import sys
import asyncio
import base64
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

# Add backend path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.rtsp_camera import RTSPCamera
from app.services.vintern_client import VinternClient

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Vintern Camera Analysis API",
    description="Integrated API for camera capture and VLM analysis",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
cameras: Dict[int, RTSPCamera] = {}
vlm_client: Optional[VinternClient] = None


# Request/Response Models
class AnalyzeRequest(BaseModel):
    camera_id: int = 1
    prompt: str = "Describe what you see in this image."
    save_frame: bool = False
    max_tokens: int = 512


class AnalyzeResponse(BaseModel):
    success: bool
    camera_id: int
    response: Optional[str] = None
    error: Optional[str] = None
    latency_ms: float
    timestamp: str
    frame_saved: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global cameras, vlm_client
    
    logger.info("Starting Vintern Camera Analysis Service...")
    
    # Camera credentials
    camera_user = os.getenv("CAMERA_USERNAME", "admin")
    camera_pass = os.getenv("CAMERA_PASSWORD", "abcd12345")
    
    # Initialize cameras
    for cam_id in [1, 2]:
        camera_ip = os.getenv(f"CAMERA{cam_id}_IP", f"192.168.1.{4 if cam_id == 1 else 7}")
        rtsp_url = f"rtsp://{camera_user}:{camera_pass}@{camera_ip}/cam/realmonitor?channel=1&subtype=1"
        
        cameras[cam_id] = RTSPCamera(
            camera_url=rtsp_url,
            camera_name=f"Camera_{cam_id}"
        )
        logger.info(f"Camera {cam_id} configured: {camera_ip}")
    
    # Initialize VLM client
    hf_token = os.getenv("HUGGINGFACE_TOKEN", "")
    vllm_url = os.getenv("VLLM_SERVICE_URL", "http://192.168.1.16:8003")
    backend = os.getenv("VLM_BACKEND", "hf")  # hf, vllm, or pc
    
    vlm_client = VinternClient(
        hf_token=hf_token,
        vllm_url=vllm_url,
        backend=backend
    )
    
    logger.info(f"VLM Client initialized with backend: {backend}")
    logger.info("✅ Service ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down...")
    
    # Release cameras
    for cam_id, camera in cameras.items():
        camera.release()
    
    logger.info("✅ Shutdown complete")


@app.get("/")
async def root():
    """Serve Web UI"""
    web_ui_path = Path(__file__).parent / "web_ui" / "app.html"
    if web_ui_path.exists():
        return FileResponse(web_ui_path)
    else:
        return {
            "service": "Vintern Camera Analysis API",
            "status": "running",
            "cameras": [1, 2],
            "endpoints": {
                "health": "/health",
                "analyze": "/api/analyze (POST)",
                "capture": "/api/capture/{camera_id}",
                "cameras": "/api/cameras",
                "web_ui": "/web (if available)"
            }
        }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "cameras_available": len(cameras),
        "vlm_backend": vlm_client.backend if vlm_client else "none"
    }


@app.get("/api/cameras")
async def list_cameras():
    """List available cameras"""
    return {
        "cameras": [
            {
                "id": cam_id,
                "name": camera.camera_name,
                "connected": camera.is_connected
            }
            for cam_id, camera in cameras.items()
        ]
    }


@app.get("/api/capture/{camera_id}")
async def capture_frame(camera_id: int):
    """Capture a single frame from camera"""
    if camera_id not in cameras:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
    
    camera = cameras[camera_id]
    result = camera.capture_frame()
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to capture frame")
    
    _, frame_bytes = result
    
    return StreamingResponse(
        iter([frame_bytes]),
        media_type="image/jpeg",
        headers={"Content-Disposition": f"inline; filename=camera_{camera_id}.jpg"}
    )


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_camera(request: AnalyzeRequest):
    """Capture frame and analyze with VLM"""
    
    if request.camera_id not in cameras:
        return AnalyzeResponse(
            success=False,
            camera_id=request.camera_id,
            error=f"Camera {request.camera_id} not found",
            latency_ms=0,
            timestamp=datetime.now().isoformat()
        )
    
    # Capture frame
    camera = cameras[request.camera_id]
    result = camera.capture_frame()
    
    if not result:
        return AnalyzeResponse(
            success=False,
            camera_id=request.camera_id,
            error="Failed to capture frame",
            latency_ms=0,
            timestamp=datetime.now().isoformat()
        )
    
    _, frame_bytes = result
    logger.info(f"Captured frame from Camera {request.camera_id}: {len(frame_bytes)} bytes")
    
    # Save frame if requested
    frame_path = None
    if request.save_frame:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        frame_path = output_dir / f"camera_{request.camera_id}_{timestamp}.jpg"
        with open(frame_path, 'wb') as f:
            f.write(frame_bytes)
        logger.info(f"Frame saved: {frame_path}")
    
    # Analyze with VLM
    if not vlm_client:
        return AnalyzeResponse(
            success=False,
            camera_id=request.camera_id,
            error="VLM client not initialized",
            latency_ms=0,
            timestamp=datetime.now().isoformat(),
            frame_saved=str(frame_path) if frame_path else None
        )
    
    vlm_result = vlm_client.analyze_image(frame_bytes, request.prompt, request.max_tokens)
    
    return AnalyzeResponse(
        success=vlm_result['success'],
        camera_id=request.camera_id,
        response=vlm_result.get('response'),
        error=vlm_result.get('error'),
        latency_ms=vlm_result['latency_ms'],
        timestamp=datetime.now().isoformat(),
        frame_saved=str(frame_path) if frame_path else None
    )


@app.get("/api/monitor/{camera_id}")
async def monitor_camera(camera_id: int, interval: int = 5, max_iterations: int = 10):
    """
    Monitor camera continuously and analyze frames
    Returns analysis results as they come
    """
    if camera_id not in cameras:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
    
    async def generate():
        camera = cameras[camera_id]
        prompt = "Mô tả chi tiết những gì bạn thấy. Có người không? Có xe không?"
        
        for i in range(max_iterations):
            # Capture
            result = camera.capture_frame()
            if not result:
                yield f"data: {{'error': 'Failed to capture frame'}}\n\n"
                await asyncio.sleep(interval)
                continue
            
            _, frame_bytes = result
            
            # Analyze
            vlm_result = vlm_client.analyze_image(frame_bytes, prompt)
            
            # Send result
            import json
            data = {
                "iteration": i + 1,
                "camera_id": camera_id,
                "success": vlm_result['success'],
                "response": vlm_result.get('response'),
                "error": vlm_result.get('error'),
                "latency_ms": vlm_result['latency_ms'],
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(data)}\n\n"
            
            # Wait
            if i < max_iterations - 1:
                await asyncio.sleep(interval)
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


if __name__ == "__main__":
    # Get configuration
    host = os.getenv("HOST_IP", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8001"))
    
    print("=" * 70)
    print("🚀 Starting Vintern Camera Analysis Service")
    print("=" * 70)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"URL: http://{host}:{port}")
    print(f"Docs: http://{host}:{port}/docs")
    print("=" * 70)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
