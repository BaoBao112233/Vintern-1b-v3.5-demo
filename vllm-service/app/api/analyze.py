"""
VLLM Analysis API Endpoints
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.vllm import get_vllm

logger = logging.getLogger(__name__)

router = APIRouter()


class AnalysisRequest(BaseModel):
    """Request model for image analysis"""
    image_description: str
    detected_objects: Optional[List[Dict[str, Any]]] = None
    question: Optional[str] = None
    max_new_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9


class AnalysisResponse(BaseModel):
    """Response model for analysis"""
    success: bool
    response: str
    context: Dict[str, Any] = {}


class ChatRequest(BaseModel):
    """Request model for chat"""
    message: str
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response model for chat"""
    success: bool
    message: str


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(request: AnalysisRequest):
    """
    Analyze image with context from detection service
    
    Args:
        request: Analysis request with image description and context
        
    Returns:
        AI-generated analysis
    """
    try:
        vllm = await get_vllm()
        
        if not vllm.is_ready():
            raise HTTPException(status_code=503, detail="VLLM not ready")
        
        # Generate response
        response = await vllm.analyze(
            image_description=request.image_description,
            detected_objects=request.detected_objects,
            question=request.question,
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature,
            top_p=request.top_p
        )
        
        return AnalysisResponse(
            success=True,
            response=response,
            context={
                "detected_objects_count": len(request.detected_objects) if request.detected_objects else 0,
                "has_question": request.question is not None
            }
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Simple chat endpoint
    
    Args:
        request: Chat request
        
    Returns:
        AI response
    """
    try:
        vllm = await get_vllm()
        
        if not vllm.is_ready():
            raise HTTPException(status_code=503, detail="VLLM not ready")
        
        # Extract context if available
        detected_objects = request.context.get("detected_objects") if request.context else None
        image_desc = request.context.get("image_description", "") if request.context else ""
        
        # Generate response
        response = await vllm.analyze(
            image_description=image_desc,
            detected_objects=detected_objects,
            question=request.message
        )
        
        return ChatResponse(
            success=True,
            message=response
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-info")
async def get_model_info():
    """Get VLLM model information"""
    try:
        vllm = await get_vllm()
        return vllm.get_model_info()
    except Exception as e:
        return {
            "error": str(e),
            "is_loaded": False
        }
