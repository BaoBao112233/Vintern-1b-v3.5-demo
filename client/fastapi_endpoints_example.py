#!/usr/bin/env python3
"""
FastAPI Endpoints Example cho Raspberry Pi Backend

Copy code này vào backend/app/api/vision.py hoặc tạo file mới
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import logging

# Import vision service (adjust path based on your structure)
from .vision_service_example import VisionAIService

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/vision", tags=["vision"])

# Initialize service (singleton - chỉ tạo 1 lần)
# TODO: Thay 192.168.1.3 bằng IP thực của PC
vision_service = VisionAIService(
    pc_host="192.168.1.3",
    pc_port=8080,
    timeout=60
)


# ============================================================================
# Pydantic Models
# ============================================================================

class YOLODetection(BaseModel):
    """YOLO detection result"""
    label: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]


class VisionAnalysisResponse(BaseModel):
    """Standard response format"""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/health")
async def health_check():
    """
    Kiểm tra PC inference server có available không
    
    GET /api/vision/health
    
    Returns:
        {"success": true, "pc_server_available": true}
    """
    try:
        is_available = vision_service.health_check()
        
        return {
            "success": True,
            "pc_server_available": is_available,
            "message": "PC server is available" if is_available else "PC server offline"
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "success": False,
            "pc_server_available": False,
            "error": str(e)
        }


@router.post("/analyze/quick", response_model=VisionAnalysisResponse)
async def analyze_quick(
    file: UploadFile = File(..., description="Image file (JPEG/PNG)")
):
    """
    Phân tích nhanh - Single-turn inference
    
    POST /api/vision/analyze/quick
    Content-Type: multipart/form-data
    
    Use case:
    - Real-time monitoring
    - Quick description
    - Low latency required
    
    Returns:
        {
            "success": true,
            "data": {
                "description": "Hình ảnh chụp...",
                "tokens": 342,
                "latency_ms": 2345.67
            }
        }
    """
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="File must be an image (JPEG/PNG)"
            )
        
        # Read image data
        image_data = await file.read()
        
        # Simple analysis
        result = vision_service.analyze_simple(image_data)
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Analysis failed")
            )
        
        logger.info(
            f"Quick analysis: {result['tokens']} tokens, "
            f"{result['latency_ms']}ms"
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/detailed", response_model=VisionAnalysisResponse)
async def analyze_detailed(
    file: UploadFile = File(..., description="Image file (JPEG/PNG)")
):
    """
    Phân tích chi tiết - Multi-turn comprehensive analysis
    
    POST /api/vision/analyze/detailed
    Content-Type: multipart/form-data
    
    Use case:
    - Comprehensive description needed
    - Quality over speed
    - Detailed object analysis
    
    Returns:
        {
            "success": true,
            "data": {
                "summary": "Full comprehensive description...",
                "phases": {
                    "overview": "...",
                    "objects": "...",
                    "details": "...",
                    "context": "..."
                },
                "total_tokens": 1234,
                "total_time_ms": 5678.9
            }
        }
    """
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )
        
        # Read image data
        image_data = await file.read()
        
        # Comprehensive analysis
        result = vision_service.analyze_comprehensive(image_data)
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Analysis failed")
            )
        
        logger.info(
            f"Detailed analysis: {result['total_tokens']} tokens, "
            f"{result['total_time_ms']}ms"
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detailed analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/with-yolo", response_model=VisionAnalysisResponse)
async def analyze_with_yolo(
    file: UploadFile = File(..., description="Image file"),
    detections: str = Body(..., description="YOLO detections as JSON string")
):
    """
    Phân tích kết hợp YOLO detection results
    
    POST /api/vision/analyze/with-yolo
    Content-Type: multipart/form-data
    
    Body:
        - file: Image file
        - detections: JSON string of YOLO results, e.g.:
          '[{"label": "person", "confidence": 0.95, "bbox": [100, 150, 300, 450]}]'
    
    Use case:
    - Verify YOLO detections with VLM
    - Get detailed description of detected objects
    - Calculate confidence score
    
    Returns:
        {
            "success": true,
            "data": {
                "vlm_description": "...",
                "yolo_detections": [...],
                "verification": "confirmed",
                "confidence": 0.85
            }
        }
    """
    try:
        import json
        
        # Validate file
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Parse YOLO detections
        try:
            yolo_results = json.loads(detections)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON for detections"
            )
        
        # Read image
        image_data = await file.read()
        
        # Analyze with YOLO integration
        result = vision_service.analyze_with_yolo(image_data, yolo_results)
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Analysis failed")
            )
        
        logger.info(
            f"YOLO+VLM analysis: {len(yolo_results)} objects, "
            f"confidence={result['confidence']:.2f}"
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"YOLO+VLM analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/custom")
async def analyze_custom(
    file: UploadFile = File(...),
    prompt: str = Body(..., description="Custom analysis prompt")
):
    """
    Phân tích với custom prompt
    
    POST /api/vision/analyze/custom
    
    Body:
        - file: Image file
        - prompt: Custom prompt (Vietnamese or English), e.g.:
          "Có bao nhiêu người trong ảnh?"
          "Is there any suspicious activity?"
    
    Use case:
    - Specific question about image
    - Custom analysis requirements
    - Flexible querying
    """
    try:
        # Validate
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Invalid image")
        
        if not prompt or len(prompt.strip()) < 5:
            raise HTTPException(
                status_code=400,
                detail="Prompt must be at least 5 characters"
            )
        
        # Read image
        image_data = await file.read()
        
        # Analyze with custom prompt
        result = vision_service.analyze_simple(
            image=image_data,
            custom_prompt=prompt
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Analysis failed")
            )
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Custom analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Integration với existing RTSP/detection pipeline
# ============================================================================

@router.post("/analyze/rtsp-frame")
async def analyze_rtsp_frame(
    camera_id: str = Body(...),
    frame_data: str = Body(..., description="Base64 encoded frame"),
    include_detections: bool = Body(default=True)
):
    """
    Phân tích một frame từ RTSP camera
    
    POST /api/vision/analyze/rtsp-frame
    
    Body:
        {
            "camera_id": "camera_1",
            "frame_data": "base64_encoded_jpeg",
            "include_detections": true
        }
    
    Use case:
    - Integrate với existing RTSP pipeline
    - Analyze specific frames on demand
    - Triggered by events (motion detection, schedule, etc.)
    """
    try:
        import base64
        
        # Decode frame
        try:
            frame_bytes = base64.b64decode(frame_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 data")
        
        # Analyze
        result = vision_service.analyze_simple(frame_bytes)
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail="Analysis failed"
            )
        
        # Add metadata
        result["camera_id"] = camera_id
        result["timestamp"] = __import__("datetime").datetime.now().isoformat()
        
        logger.info(f"RTSP frame analyzed: camera={camera_id}")
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RTSP frame analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# How to use this file
# ============================================================================

"""
USAGE IN YOUR FASTAPI APP:

1. Copy this file to: backend/app/api/vision_endpoints.py

2. In backend/app/main.py:
   
   from fastapi import FastAPI
   from .api import vision_endpoints
   
   app = FastAPI()
   app.include_router(vision_endpoints.router)

3. Install dependencies:
   pip install fastapi python-multipart pillow requests

4. Start server:
   uvicorn app.main:app --host 0.0.0.0 --port 8000

5. Test endpoints:
   curl -X POST http://localhost:8000/api/vision/health
   
   curl -X POST http://localhost:8000/api/vision/analyze/quick \\
     -F "file=@test.jpg"
   
   curl -X POST http://localhost:8000/api/vision/analyze/detailed \\
     -F "file=@test.jpg"

6. API Docs:
   http://localhost:8000/docs
"""
