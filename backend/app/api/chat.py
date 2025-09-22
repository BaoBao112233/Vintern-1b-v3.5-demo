"""
Enhanced Chat API với object detection và local model
"""

import json
import base64
import cv2
import numpy as np
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from PIL import Image
import io

from app.services.local_model import get_local_model
from app.services.object_detection import get_object_detector
from app.services.hf_client import HuggingFaceClient

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    image_data: Optional[str] = None  # Base64 encoded image
    include_objects: bool = True
    confidence_threshold: float = 0.5

class ChatResponse(BaseModel):
    response: str
    detected_objects: List[Dict[str, Any]] = []
    objects_summary: str = ""
    image_with_boxes: Optional[str] = None  # Base64 encoded

@router.post("/chat", response_model=ChatResponse)
async def chat_with_vision(request: ChatRequest):
    """Chat endpoint với vision và object detection"""
    try:
        detected_objects = []
        objects_summary = ""
        image_with_boxes = None
        
        # Nếu có ảnh, xử lý object detection
        if request.image_data and request.include_objects:
            # Decode base64 image
            image_data = base64.b64decode(request.image_data.split(',')[1] if ',' in request.image_data else request.image_data)
            image = Image.open(io.BytesIO(image_data))
            image_np = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Object detection
            detector = await get_object_detector()
            if detector.is_available():
                detected_objects = await detector.detect_objects(image_np)
                detected_objects = detector.filter_objects_by_confidence(
                    detected_objects, 
                    request.confidence_threshold
                )
                objects_summary = detector.get_objects_summary(detected_objects)
                
                # Vẽ bounding boxes
                image_with_boxes_np = detector.draw_bounding_boxes(image_np, detected_objects)
                _, buffer = cv2.imencode('.jpg', image_with_boxes_np)
                image_with_boxes = base64.b64encode(buffer).decode('utf-8')
        
        # Generate response từ model
        model = await get_local_model()
        if model.is_available():
            response = await model.analyze_image_with_context(
                image_description="Ảnh từ camera" if request.image_data else "Không có ảnh",
                detected_objects=detected_objects,
                user_question=request.message
            )
        else:
            # Fallback response nếu model không available
            if detected_objects:
                response = f"Tôi thấy {objects_summary}. Về câu hỏi '{request.message}' của bạn: Xin lỗi, model hiện tại không khả dụng để phân tích chi tiết."
            else:
                response = "Xin lỗi, cả model và object detection đều không khả dụng hiện tại."
        
        return ChatResponse(
            response=response,
            detected_objects=detected_objects,
            objects_summary=objects_summary,
            image_with_boxes=image_with_boxes
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý chat: {str(e)}")

@router.post("/analyze-image")
async def analyze_image_only(file: UploadFile = File(...)):
    """Chỉ phân tích ảnh để detect objects"""
    try:
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image_np = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Object detection
        detector = await get_object_detector()
        if not detector.is_available():
            raise HTTPException(status_code=503, detail="Object detector không khả dụng")
        
        detected_objects = await detector.detect_objects(image_np)
        objects_summary = detector.get_objects_summary(detected_objects)
        
        # Vẽ bounding boxes
        image_with_boxes_np = detector.draw_bounding_boxes(image_np, detected_objects)
        _, buffer = cv2.imencode('.jpg', image_with_boxes_np)
        image_with_boxes = base64.b64encode(buffer).decode('utf-8')
        
        return {
            "detected_objects": detected_objects,
            "objects_summary": objects_summary,
            "image_with_boxes": image_with_boxes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi phân tích ảnh: {str(e)}")

@router.get("/model-status")
async def get_model_status():
    """Lấy trạng thái của model và object detector"""
    model = await get_local_model()
    detector = await get_object_detector()
    
    return {
        "local_model": {
            "available": model.is_available(),
            "info": model.get_model_info() if model.is_available() else None
        },
        "object_detector": {
            "available": detector.is_available(),
            "model_name": detector.model_name if detector.is_available() else None
        }
    }