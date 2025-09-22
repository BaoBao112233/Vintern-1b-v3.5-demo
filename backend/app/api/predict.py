"""
API routes for prediction endpoints
"""
import os
import time
import base64
import logging
from typing import Optional
from io import BytesIO
from PIL import Image
import numpy as np

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.services.hf_client import HuggingFaceClient
from app.services.local_runner import LocalRunner
from app.utils.image_processing import process_image, encode_result_image

logger = logging.getLogger(__name__)

router = APIRouter()

class PredictRequest(BaseModel):
    """Request model for single image prediction"""
    image_base64: str
    frame_id: Optional[str] = None
    timestamp: Optional[float] = None
    resize_width: Optional[int] = 640
    resize_height: Optional[int] = 480

class PredictResponse(BaseModel):
    """Response model for prediction results"""
    frame_id: Optional[str] = None
    timestamp: float
    processing_time: float
    success: bool
    error: Optional[str] = None
    results: Optional[dict] = None
    result_image_base64: Optional[str] = None

def get_model_service():
    """Get the appropriate model service based on configuration"""
    from app.main import hf_client, local_runner
    
    model_mode = os.getenv("MODEL_MODE", "hf").lower()
    
    if model_mode == "hf":
        if not hf_client or not hf_client.is_ready():
            raise HTTPException(
                status_code=503, 
                detail="Hugging Face client not ready"
            )
        return hf_client
    elif model_mode == "local":
        if not local_runner or not local_runner.is_ready():
            raise HTTPException(
                status_code=503, 
                detail="Local model runner not ready"
            )
        return local_runner
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Invalid model mode: {model_mode}"
        )

@router.post("/predict", response_model=PredictResponse)
async def predict_single_image(request: PredictRequest):
    """
    Predict on a single image sent as base64
    """
    start_time = time.time()
    
    try:
        # Decode base64 image
        try:
            image_data = base64.b64decode(request.image_base64)
            image = Image.open(BytesIO(image_data))
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid base64 image data: {str(e)}"
            )
        
        # Process image
        processed_image = process_image(
            image, 
            target_width=request.resize_width, 
            target_height=request.resize_height
        )
        
        # Get model service and run inference
        model_service = get_model_service()
        results = await model_service.predict(processed_image)
        
        # Encode result image if available
        result_image_base64 = None
        if "annotated_image" in results:
            result_image_base64 = encode_result_image(results["annotated_image"])
        
        processing_time = time.time() - start_time
        
        return PredictResponse(
            frame_id=request.frame_id,
            timestamp=request.timestamp or time.time(),
            processing_time=processing_time,
            success=True,
            results=results,
            result_image_base64=result_image_base64
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Prediction error: {str(e)}")
        
        return PredictResponse(
            frame_id=request.frame_id,
            timestamp=request.timestamp or time.time(),
            processing_time=processing_time,
            success=False,
            error=str(e)
        )

@router.post("/predict/upload", response_model=PredictResponse)
async def predict_upload_image(
    file: UploadFile = File(...),
    frame_id: Optional[str] = Form(None),
    resize_width: int = Form(640),
    resize_height: int = Form(480)
):
    """
    Predict on an uploaded image file
    """
    start_time = time.time()
    
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, 
                detail="File must be an image"
            )
        
        # Read and process image
        image_data = await file.read()
        image = Image.open(BytesIO(image_data))
        
        processed_image = process_image(
            image, 
            target_width=resize_width, 
            target_height=resize_height
        )
        
        # Get model service and run inference
        model_service = get_model_service()
        results = await model_service.predict(processed_image)
        
        # Encode result image if available
        result_image_base64 = None
        if "annotated_image" in results:
            result_image_base64 = encode_result_image(results["annotated_image"])
        
        processing_time = time.time() - start_time
        
        return PredictResponse(
            frame_id=frame_id,
            timestamp=time.time(),
            processing_time=processing_time,
            success=True,
            results=results,
            result_image_base64=result_image_base64
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Upload prediction error: {str(e)}")
        
        return PredictResponse(
            frame_id=frame_id,
            timestamp=time.time(),
            processing_time=processing_time,
            success=False,
            error=str(e)
        )