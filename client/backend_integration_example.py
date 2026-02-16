#!/usr/bin/env python3
"""
Backend Integration Example

Ví dụ tích hợp PC inference client vào FastAPI backend trên Raspberry Pi
"""

import asyncio
import logging
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import cv2
import numpy as np
from PIL import Image

# Import client (adjust path as needed)
import sys
sys.path.append('/path/to/client')  # Adjust this
from pc_inference_client import PCInferenceClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Pi Backend with PC Inference")

# Global PC client
pc_client: Optional[PCInferenceClient] = None

# Request/Response models
class InferenceRequest(BaseModel):
    camera_id: int
    prompt: str = "Mô tả những gì bạn thấy"
    max_tokens: int = 200
    temperature: float = 0.1

class InferenceResponse(BaseModel):
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    elapsed_time: float = 0
    camera_id: int


@app.on_event("startup")
async def startup_event():
    """Initialize PC client on startup"""
    global pc_client
    
    # PC IP - THAY ĐỔI CHỖ NÀY!
    PC_HOST = "192.168.1.100"  # <-- Sửa thành IP của PC
    
    logger.info(f"Connecting to PC inference server at {PC_HOST}:8080")
    
    pc_client = PCInferenceClient(
        pc_host=PC_HOST,
        timeout=30,
        max_retries=3
    )
    
    # Health check
    if pc_client.health_check():
        logger.info("✅ PC inference server is ready")
    else:
        logger.warning("⚠️ PC inference server is not responding")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global pc_client
    if pc_client:
        pc_client.close()
        logger.info("PC client closed")


@app.get("/health")
async def health_check():
    """Backend health check"""
    pc_status = pc_client.health_check() if pc_client else False
    
    return {
        "backend": "ok",
        "pc_inference": "ok" if pc_status else "error"
    }


@app.post("/inference", response_model=InferenceResponse)
async def run_inference(request: InferenceRequest):
    """
    Run inference on current frame from camera
    
    This is a simplified example. In production:
    - Capture frame from actual camera/RTSP stream
    - Add frame buffering
    - Add detection pipeline
    """
    if not pc_client:
        raise HTTPException(status_code=500, detail="PC client not initialized")
    
    # TODO: Replace with actual frame capture
    # For now, assume we have a saved frame
    frame_path = f"/tmp/camera_{request.camera_id}_frame.jpg"
    
    try:
        # Run inference in thread pool to not block event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            pc_client.chat_completion,
            frame_path,
            request.prompt,
            request.max_tokens,
            request.temperature
        )
        
        if "error" in result:
            return InferenceResponse(
                success=False,
                error=result["error"],
                elapsed_time=result.get("elapsed_time", 0),
                camera_id=request.camera_id
            )
        else:
            return InferenceResponse(
                success=True,
                content=result["content"],
                elapsed_time=result["elapsed_time"],
                camera_id=request.camera_id
            )
            
    except Exception as e:
        logger.error(f"Inference error: {e}")
        return InferenceResponse(
            success=False,
            error=str(e),
            camera_id=request.camera_id
        )


@app.post("/inference-with-detections")
async def inference_with_detections(
    camera_id: int,
    detections: list,
    prompt: Optional[str] = None
):
    """
    Run inference với detected objects
    
    Example detections:
    [
        {"class": "person", "confidence": 0.95, "bbox": [x,y,w,h]},
        {"class": "car", "confidence": 0.88, "bbox": [x,y,w,h]}
    ]
    """
    if not pc_client:
        raise HTTPException(status_code=500, detail="PC client not initialized")
    
    frame_path = f"/tmp/camera_{camera_id}_frame.jpg"
    
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            pc_client.analyze_detections,
            frame_path,
            detections,
            prompt
        )
        
        return {
            "success": "error" not in result,
            "content": result.get("content"),
            "error": result.get("error"),
            "elapsed_time": result.get("elapsed_time", 0),
            "camera_id": camera_id,
            "num_detections": len(detections)
        }
        
    except Exception as e:
        logger.error(f"Inference error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Camera Integration Example (with OpenCV)
# ============================================================================

class CameraManager:
    """Manage RTSP camera streams"""
    
    def __init__(self):
        self.cameras: Dict[int, cv2.VideoCapture] = {}
        self.latest_frames: Dict[int, np.ndarray] = {}
    
    def add_camera(self, camera_id: int, rtsp_url: str):
        """Add camera stream"""
        logger.info(f"Adding camera {camera_id}: {rtsp_url}")
        cap = cv2.VideoCapture(rtsp_url)
        
        if cap.isOpened():
            self.cameras[camera_id] = cap
            logger.info(f"✅ Camera {camera_id} connected")
            return True
        else:
            logger.error(f"❌ Failed to connect camera {camera_id}")
            return False
    
    def capture_frame(self, camera_id: int) -> Optional[Image.Image]:
        """Capture current frame from camera"""
        if camera_id not in self.cameras:
            logger.warning(f"Camera {camera_id} not found")
            return None
        
        cap = self.cameras[camera_id]
        ret, frame = cap.read()
        
        if ret:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            return pil_image
        else:
            logger.warning(f"Failed to capture frame from camera {camera_id}")
            return None
    
    def close_all(self):
        """Close all camera streams"""
        for camera_id, cap in self.cameras.items():
            cap.release()
            logger.info(f"Camera {camera_id} released")
        self.cameras.clear()


# Global camera manager
camera_manager = CameraManager()


@app.post("/camera/add")
async def add_camera(camera_id: int, rtsp_url: str):
    """Add RTSP camera stream"""
    success = camera_manager.add_camera(camera_id, rtsp_url)
    
    if success:
        return {"success": True, "camera_id": camera_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to connect camera")


@app.post("/camera/{camera_id}/analyze")
async def analyze_camera(camera_id: int, prompt: str = "Mô tả tình hình"):
    """Capture frame từ camera và analyze"""
    if not pc_client:
        raise HTTPException(status_code=500, detail="PC client not initialized")
    
    # Capture frame
    frame = camera_manager.capture_frame(camera_id)
    if frame is None:
        raise HTTPException(status_code=404, detail="Failed to capture frame")
    
    # Run inference
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            pc_client.chat_completion,
            frame,
            prompt
        )
        
        return {
            "success": "error" not in result,
            "content": result.get("content"),
            "error": result.get("error"),
            "elapsed_time": result.get("elapsed_time", 0),
            "camera_id": camera_id
        }
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_cameras():
    """Close all cameras on shutdown"""
    camera_manager.close_all()


# ============================================================================
# WebSocket Support (Optional - for real-time streaming)
# ============================================================================

from fastapi import WebSocket

@app.websocket("/ws/camera/{camera_id}")
async def websocket_camera(websocket: WebSocket, camera_id: int):
    """
    WebSocket endpoint for real-time camera analysis
    
    Usage:
        ws = new WebSocket("ws://pi-ip:8001/ws/camera/1")
        ws.send(JSON.stringify({prompt: "What do you see?"}))
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive prompt from client
            data = await websocket.receive_json()
            prompt = data.get("prompt", "Mô tả tình hình")
            
            # Capture frame
            frame = camera_manager.capture_frame(camera_id)
            if frame is None:
                await websocket.send_json({
                    "error": "Failed to capture frame"
                })
                continue
            
            # Run inference
            result = pc_client.chat_completion(frame, prompt)
            
            # Send result
            await websocket.send_json({
                "camera_id": camera_id,
                "content": result.get("content"),
                "error": result.get("error"),
                "elapsed_time": result.get("elapsed_time", 0)
            })
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()


# ============================================================================
# Run server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Development mode
    uvicorn.run(
        "backend_integration_example:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
