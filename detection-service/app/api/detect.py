"""
Detection API Endpoints
"""

import io
import base64
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import numpy as np
from PIL import Image
import cv2

from app.models.detector import get_detector

logger = logging.getLogger(__name__)

router = APIRouter()


class DetectionRequest(BaseModel):
    """Request model for detection"""
    image_base64: str
    draw_boxes: bool = False


class DetectionResponse(BaseModel):
    """Response model for detection"""
    success: bool
    detections: List[Dict[str, Any]]
    summary: str
    image_with_boxes: str = None


@router.post("/detect", response_model=DetectionResponse)
async def detect_objects(request: DetectionRequest):
    """
    Detect objects in base64-encoded image
    
    Args:
        request: Detection request with base64 image
        
    Returns:
        Detection results with optional bounding boxes
    """
    try:
        detector = await get_detector()
        
        if not detector.is_ready():
            raise HTTPException(status_code=503, detail="Detector not ready")
        
        # Decode base64 image
        image_bytes = base64.b64decode(request.image_base64)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to numpy array (BGR for OpenCV)
        image_np = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Detect objects
        detections = await detector.detect(image_np)
        
        # Get summary
        summary = detector.get_summary(detections)
        
        # Draw boxes if requested
        image_with_boxes_b64 = None
        if request.draw_boxes and detections:
            image_with_boxes = detector.draw_bounding_boxes(image_np, detections)
            
            # Encode to base64
            _, buffer = cv2.imencode('.jpg', image_with_boxes)
            image_with_boxes_b64 = base64.b64encode(buffer).decode('utf-8')
        
        return DetectionResponse(
            success=True,
            detections=detections,
            summary=summary,
            image_with_boxes=image_with_boxes_b64
        )
        
    except Exception as e:
        logger.error(f"Detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect/upload", response_model=DetectionResponse)
async def detect_from_upload(
    file: UploadFile = File(...),
    draw_boxes: bool = False
):
    """
    Detect objects from uploaded image file
    
    Args:
        file: Uploaded image file
        draw_boxes: Whether to draw bounding boxes
        
    Returns:
        Detection results
    """
    try:
        detector = await get_detector()
        
        if not detector.is_ready():
            raise HTTPException(status_code=503, detail="Detector not ready")
        
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Convert to numpy array
        image_np = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Detect
        detections = await detector.detect(image_np)
        summary = detector.get_summary(detections)
        
        # Draw boxes
        image_with_boxes_b64 = None
        if draw_boxes and detections:
            image_with_boxes = detector.draw_bounding_boxes(image_np, detections)
            _, buffer = cv2.imencode('.jpg', image_with_boxes)
            image_with_boxes_b64 = base64.b64encode(buffer).decode('utf-8')
        
        return DetectionResponse(
            success=True,
            detections=detections,
            summary=summary,
            image_with_boxes=image_with_boxes_b64
        )
        
    except Exception as e:
        logger.error(f"Upload detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Get detector status"""
    try:
        detector = await get_detector()
        
        return {
            "ready": detector.is_ready(),
            "model_path": detector.model_path,
            "confidence_threshold": detector.confidence_threshold,
            "labels_count": len(detector.labels)
        }
        
    except Exception as e:
        return {
            "ready": False,
            "error": str(e)
        }
