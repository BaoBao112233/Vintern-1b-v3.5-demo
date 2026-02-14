"""
Multi-Camera API endpoints
Handle multiple RTSP camera streams with object detection
"""

import logging
import base64
import asyncio
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import cv2
import numpy as np

from app.services.camera_manager import get_camera_manager, initialize_cameras
from app.services.detection_client import get_detection_client
logger = logging.getLogger(__name__)

router = APIRouter()


class CameraFrame(BaseModel):
    """Camera frame data"""
    camera_id: str
    frame_base64: str
    timestamp: int


class MultiCameraResponse(BaseModel):
    """Response for multi-camera detection"""
    success: bool
    cameras: Dict[str, Any]
    timestamp: int


@router.get("/cameras/status")
async def get_cameras_status():
    """Get status of all cameras"""
    try:
        manager = get_camera_manager()
        status = manager.get_status()
        
        return {
            "success": True,
            "cameras": status,
            "count": len(status)
        }
    except Exception as e:
        logger.error(f"Error getting camera status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cameras/initialize")
async def initialize_all_cameras():
    """Initialize all configured cameras"""
    try:
        manager = await initialize_cameras()
        status = manager.get_status()
        
        return {
            "success": True,
            "message": "Cameras initialized",
            "cameras": status
        }
    except Exception as e:
        logger.error(f"Error initializing cameras: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cameras/{camera_id}/frame")
async def get_camera_frame(camera_id: str, detect: bool = True):
    """Get latest frame from specific camera with optional detection"""
    try:
        manager = get_camera_manager()
        frame = manager.get_frame(camera_id)
        
        if frame is None:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found or no frame available")
        
        result = {
            "success": True,
            "camera_id": camera_id,
            "detections": []
        }
        
        # Perform detection if requested
        if detect:
            detection_client = await get_detection_client()
            if detection_client.is_ready():
                detection_result = await detection_client.detect_objects(frame, draw_boxes=True)
                result["detections"] = detection_result.get("detections", [])
                result["summary"] = detection_result.get("summary", "")
                
                # Return image with boxes if available
                if detection_result.get("image_with_boxes"):
                    result["image_base64"] = detection_result["image_with_boxes"]
                else:
                    _, buffer = cv2.imencode('.jpg', frame)
                    result["image_base64"] = base64.b64encode(buffer).decode('utf-8')
            else:
                # Just return the frame without detection
                _, buffer = cv2.imencode('.jpg', frame)
                result["image_base64"] = base64.b64encode(buffer).decode('utf-8')
        else:
            # Return frame without detection
            _, buffer = cv2.imencode('.jpg', frame)
            result["image_base64"] = base64.b64encode(buffer).decode('utf-8')
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting camera frame: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cameras/all/frames")
async def get_all_camera_frames(detect: bool = True):
    """Get latest frames from all cameras with optional detection"""
    try:
        manager = get_camera_manager()
        frames = manager.get_all_frames()
        
        if not frames:
            return {
                "success": True,
                "cameras": {},
                "message": "No frames available"
            }
        
        result = {
            "success": True,
            "cameras": {}
        }
        
        # Process each camera frame
        detection_client = await get_detection_client() if detect else None
        
        for camera_id, frame in frames.items():
            camera_result = {
                "camera_id": camera_id,
                "detections": []
            }
            
            # Perform detection if requested and available
            if detect and detection_client and detection_client.is_ready():
                detection_result = await detection_client.detect_objects(frame, draw_boxes=True)
                camera_result["detections"] = detection_result.get("detections", [])
                camera_result["summary"] = detection_result.get("summary", "")
                
                # Use image with boxes if available
                if detection_result.get("image_with_boxes"):
                    camera_result["image_base64"] = detection_result["image_with_boxes"]
                else:
                    _, buffer = cv2.imencode('.jpg', frame)
                    camera_result["image_base64"] = base64.b64encode(buffer).decode('utf-8')
            else:
                # Return frame without detection
                _, buffer = cv2.imencode('.jpg', frame)
                camera_result["image_base64"] = base64.b64encode(buffer).decode('utf-8')
            
            result["cameras"][camera_id] = camera_result
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting all camera frames: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/cameras")
async def websocket_multi_camera(websocket: WebSocket):
    """WebSocket endpoint for real-time multi-camera streaming"""
    await websocket.accept()
    logger.info("Multi-camera WebSocket client connected")
    
    try:
        manager = get_camera_manager()
        detection_client = await get_detection_client()
        
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "cameras": manager.get_status()
        })
        
        frame_count = 0
        
        while True:
            # Get frames from all cameras
            frames = manager.get_all_frames()
            
            if not frames:
                await asyncio.sleep(0.2)
                continue
            
            frame_count += 1
            
            # Process each camera
            results = {}
            for camera_id, frame in frames.items():
                try:
                    # Detect objects
                    detection_result = await detection_client.detect_objects(frame, draw_boxes=True)
                    
                    # Prepare result
                    camera_result = {
                        "camera_id": camera_id,
                        "detections": detection_result.get("detections", []),
                        "summary": detection_result.get("summary", ""),
                        "frame_count": frame_count
                    }
                    
                    # Add image with boxes if available
                    if detection_result.get("image_with_boxes"):
                        camera_result["image_base64"] = detection_result["image_with_boxes"]
                    else:
                        _, buffer = cv2.imencode('.jpg', frame)
                        camera_result["image_base64"] = base64.b64encode(buffer).decode('utf-8')
                    
                    results[camera_id] = camera_result
                    
                except Exception as e:
                    logger.error(f"Error processing camera {camera_id}: {e}")
            
            # Send results
            if results:
                await websocket.send_json({
                    "type": "frames",
                    "cameras": results,
                    "timestamp": asyncio.get_event_loop().time()
                })
            
            # Control frame rate (e.g., 5 FPS = 200ms delay)
            await asyncio.sleep(0.2)
            
    except WebSocketDisconnect:
        logger.info("Multi-camera WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass
