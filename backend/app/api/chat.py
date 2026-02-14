"""
Enhanced Chat API với object detection và VLLM service (Orange Pi)
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
from app.services.vllm_client import get_vllm_client
from app.services.detection_client import get_detection_client

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
    """Chat endpoint với vision, object detection và VLLM service (Orange Pi)"""
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
            
            # Object detection using detection service
            detection_client = await get_detection_client()
            if detection_client.is_available():
                detected_objects = await detection_client.detect_objects(image_np)
                # Filter by confidence
                detected_objects = [
                    obj for obj in detected_objects 
                    if obj.get('confidence', 0) >= request.confidence_threshold
                ]
                
                # Create summary
                if detected_objects:
                    obj_counts = {}
                    for obj in detected_objects:
                        label = obj['label']
                        obj_counts[label] = obj_counts.get(label, 0) + 1
                    objects_summary = ", ".join([f"{count} {label}" for label, count in obj_counts.items()])
                
                # Draw bounding boxes
                for obj in detected_objects:
                    bbox = obj['bbox']
                    x1, y1, x2, y2 = bbox
                    cv2.rectangle(image_np, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    label_text = f"{obj['label']}: {obj['confidence']:.2f}"
                    cv2.putText(image_np, label_text, (x1, y1-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                _, buffer = cv2.imencode('.jpg', image_np)
                image_with_boxes = base64.b64encode(buffer).decode('utf-8')
        
        # Generate response từ VLLM service (Orange Pi)
        vllm_client = await get_vllm_client()
        if vllm_client.is_available():
            result = await vllm_client.analyze(
                image_description="Ảnh từ camera" if request.image_data else "Không có ảnh",
                detected_objects=detected_objects,
                question=request.message
            )
            response = result.get("response", "Không có phản hồi từ VLLM service")
        else:
            # Fallback response nếu VLLM không available
            if detected_objects:
                response = f"Tôi thấy {objects_summary}. VLLM service chưa sẵn sàng để phân tích chi tiết."
            else:
                response = "VLLM service chưa khả dụng. Chỉ có thể dùng detection service."
        
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
        
        # Object detection using detection service
        detection_client = await get_detection_client()
        if not detection_client.is_available():
            raise HTTPException(status_code=503, detail="Detection service không khả dụng")
        
        detected_objects = await detection_client.detect_objects(image_np)
        
        # Create summary
        if detected_objects:
            obj_counts = {}
            for obj in detected_objects:
                label = obj['label']
                obj_counts[label] = obj_counts.get(label, 0) + 1
            objects_summary = ", ".join([f"{count} {label}" for label, count in obj_counts.items()])
        else:
            objects_summary = "Không phát hiện vật thể nào"
        
        # Draw bounding boxes
        for obj in detected_objects:
            bbox = obj['bbox']
            x1, y1, x2, y2 = bbox
            cv2.rectangle(image_np, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label_text = f"{obj['label']}: {obj['confidence']:.2f}"
            cv2.putText(image_np, label_text, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        _, buffer = cv2.imencode('.jpg', image_np)
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
    """Lấy trạng thái của VLLM service và detection service"""
    vllm_client = await get_vllm_client()
    detection_client = await get_detection_client()
    
    return {
        "vllm_service": vllm_client.get_info(),
        "detection_service": {
            "available": detection_client.is_available(),
            "url": detection_client.detection_url
        }
    }