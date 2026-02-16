"""
Simplified FastAPI Backend - RTSP + Detection only
No VLM dependency
"""

import os
import logging
import asyncio
import time
import queue
import threading
import cv2
import base64
import numpy as np
from contextlib import asynccontextmanager
from typing import Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

import sys
from pathlib import Path
# Add backend to Python path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from app.services.rtsp_client import RTSPManager
from app.services.detection import DetectionService

# Load environment
load_dotenv()

# Logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
rtsp_manager: Optional[RTSPManager] = None
detector: Optional[DetectionService] = None
latest_results: Dict = {}
latest_frames: Dict = {}  # Store frames for UI streaming
results_lock = threading.Lock()
frames_lock = threading.Lock()
ws_connections = set()
processing_thread = None
running = False


def process_frames():
    """Background thread to process frames"""
    global latest_results, latest_frames, running
    
    logger.info("🎬 Frame processor started")
    
    batch = []
    
    while running:
        try:
            # Get frame
            frame_data = rtsp_manager.get_frame(timeout=0.5)
            
            if frame_data is None:
                continue
            
            batch.append(frame_data)
            
            # Process batch
            if len(batch) >= 2:
                images = [item['frame'] for item in batch]
                
                # Run detection
                detections = detector.detect(images)
                
                # Store results with annotated frames
                for frame_item, detection in zip(batch, detections):
                    camera_id = frame_item['camera_id']
                    frame = frame_item['frame']
                    
                    # Draw detection boxes
                    annotated_frame = frame.copy()
                    for det in detection.get('detections', []):
                        x1, y1, x2, y2 = det['bbox']
                        label = f"{det['class']} {det['confidence']:.2f}"
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(annotated_frame, label, (x1, y1-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    result = {
                        'camera_id': camera_id,
                        'timestamp': frame_item['timestamp'],
                        'frame_number': frame_item['frame_number'],
                        'detection_summary': detector.get_summary(detection),
                        'detection': detection
                    }
                    
                    with results_lock:
                        latest_results[camera_id] = result
                    
                    with frames_lock:
                        latest_frames[camera_id] = annotated_frame
                
                batch = []
                
        except Exception as e:
            logger.error(f"❌ Frame processing error: {e}")
            batch = []
            time.sleep(0.1)
    
    logger.info("🎬 Frame processor stopped")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown"""
    global rtsp_manager, detector, processing_thread, running
    
    logger.info("🚀 Starting Vintern Vision AI Backend")
    logger.info("=" * 70)
    
    # Get configuration
    camera_urls = {
        'camera1': os.getenv('CAMERA_1_URL'),
        'camera2': os.getenv('CAMERA_2_URL')
    }
    
    detection_device = os.getenv('DETECTION_DEVICE', 'cpu')
    detection_conf = float(os.getenv('DETECTION_CONF_THRESHOLD', '0.5'))
    sample_rate = float(os.getenv('FRAME_SAMPLE_RATE', '1.0'))
    
    if not all(camera_urls.values()):
        logger.error("❌ Camera URLs not configured")
        raise RuntimeError("Missing camera configuration")
    
    logger.info("📋 Configuration:")
    logger.info(f"   Cameras: {list(camera_urls.keys())}")
    logger.info(f"   Detection device: {detection_device}")
    logger.info(f"   Detection confidence: {detection_conf}")
    logger.info(f"   Sample rate: {sample_rate} FPS")
    
    try:
        # Initialize RTSP manager
        logger.info("\n📹 Initializing RTSP manager...")
        rtsp_manager = RTSPManager(max_queue_size=10)
        for camera_id, url in camera_urls.items():
            rtsp_manager.add_camera(camera_id, url, sample_rate)
        
        # Initialize detector
        logger.info(f"\n🔍 Initializing detector...")
        detector = DetectionService(
            model_name='yolov8n.pt',
            conf_threshold=detection_conf,
            device=detection_device,
            batch_size=2
        )
        
        # Start RTSP streams
        logger.info("\n▶️  Starting RTSP streams...")
        rtsp_manager.start_all()
        
        # Start frame processor
        logger.info("▶️  Starting frame processor...")
        running = True
        processing_thread = threading.Thread(target=process_frames, daemon=True)
        processing_thread.start()
        
        logger.info("\n✅ System started successfully")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Failed to start: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down...")
    running = False
    
    if rtsp_manager:
        rtsp_manager.stop_all()
    
    if processing_thread:
        processing_thread.join(timeout=5)
    
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Vintern Vision AI",
    description="Real-time vision AI with RTSP cameras",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    """Health check"""
    if rtsp_manager is None or detector is None:
        raise HTTPException(status_code=503, detail="System not ready")
    
    camera_status = rtsp_manager.get_all_status()
    
    return {
        "status": "healthy",
        "cameras": camera_status
    }


@app.get("/cameras")
async def get_cameras():
    """Get camera list"""
    if rtsp_manager is None:
        raise HTTPException(status_code=503, detail="System not ready")
    
    camera_status = rtsp_manager.get_all_status()
    
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
    """Get latest results"""
    with results_lock:
        formatted_results = {}
        
        for camera_id, result in latest_results.items():
            formatted_results[camera_id] = {
                "camera_id": camera_id,
                "timestamp": result.get('timestamp'),
                "frame_number": result.get('frame_number'),
                "detection": {
                    "summary": result.get('detection_summary', 'No objects'),
                    "boxes": result.get('detection', {}).get('boxes', []),
                    "classes": result.get('detection', {}).get('class_names', []),
                    "scores": result.get('detection', {}).get('scores', [])
                },
                "vlm_analysis": None  # Not available yet
            }
        
        return formatted_results


@app.get("/stats")
async def get_stats():
    """Get statistics"""
    if rtsp_manager is None:
        raise HTTPException(status_code=503, detail="System not ready")
    
    camera_status = rtsp_manager.get_all_status()
    
    total_frames = sum(s.get('frame_count', 0) for s in camera_status.values())
    
    return {
        "running": running,
        "frames_received": total_frames,
        "frames_detected": total_frames,  # Same since we process all
        "frames_analyzed": 0,  # VLM not available
        "camera_status": camera_status
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    ws_connections.add(websocket)
    
    logger.info(f"🔌 WebSocket connected (total: {len(ws_connections)})")
    
    try:
        # Send initial status
        camera_status = rtsp_manager.get_all_status() if rtsp_manager else {}
        await websocket.send_json({
            "type": "status",
            "data": {
                "running": running,
                "camera_status": camera_status
            }
        })
        
        # Stream updates
        while True:
            with results_lock:
                results_copy = dict(latest_results)
            
            # Format for frontend with frames
            formatted_results = {}
            with frames_lock:
                frames_copy = dict(latest_frames)
            
            for camera_id, result in results_copy.items():
                # Encode frame as base64 JPEG
                frame_base64 = None
                if camera_id in frames_copy:
                    frame = frames_copy[camera_id]
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                
                formatted_results[camera_id] = {
                    "detection_summary": result.get('detection_summary'),
                    "vlm_analysis": None,
                    "frame_number": result.get('frame_number'),
                    "frame": frame_base64
                }
            
            # Get stats
            total_frames = 0
            if rtsp_manager:
                camera_status = rtsp_manager.get_all_status()
                total_frames = sum(s.get('frame_count', 0) for s in camera_status.values())
            
            await websocket.send_json({
                "type": "update",
                "timestamp": time.time(),
                "results": formatted_results,
                "stats": {
                    "frames_received": total_frames,
                    "frames_detected": total_frames,
                    "frames_analyzed": 0
                }
            })
            
            await asyncio.sleep(1.0)
    
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket disconnected")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    finally:
        ws_connections.discard(websocket)
        logger.info(f"🔌 WebSocket removed (total: {len(ws_connections)})")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv('BACKEND_HOST', '0.0.0.0')
    port = int(os.getenv('BACKEND_PORT', '8001'))
    
    print("=" * 70)
    print("🚀 VINTERN VISION AI - BACKEND SERVER")
    print("=" * 70)
    print(f"📡 API:       http://{host}:{port}")
    print(f"🔌 WebSocket: ws://{host}:{port}/ws")
    print("=" * 70)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
