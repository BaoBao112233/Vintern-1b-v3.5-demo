"""
Inference API endpoint - cho phép Orange Pi VLLM proxy gọi đến
Đây là endpoint tương tự vLLM API để Orange Pi có thể forward requests
"""
import logging
import time
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class GenerateRequest(BaseModel):
    """Request model tương thích với Orange Pi VLLM proxy"""
    messages: List[Message]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9

class GenerateResponse(BaseModel):
    """Response model tương thích với Orange Pi VLLM proxy"""
    content: str
    model: str = "5CD-AI/Vintern-1B-v3_5"
    processing_time: float

@router.post("/generate")
async def generate_inference(request: GenerateRequest):
    """
    Endpoint để chạy inference trên Raspberry Pi
    Orange Pi VLLM sẽ proxy requests đến endpoint này
    """
    from app.main import local_model
    
    start_time = time.time()
    
    try:
        # Kiểm tra local model có sẵn không
        if not local_model or not local_model.is_available():
            raise HTTPException(
                status_code=503,
                detail="Local model not available. Please run setup_local_inference.sh to download and configure the model."
            )
        
        # Convert messages thành prompt
        # Lấy message cuối cùng (từ user)
        user_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_message = msg.content
                break
        
        if not user_message:
            raise HTTPException(
                status_code=400,
                detail="No user message found in request"
            )
        
        logger.info(f"🔍 Generating response for: {user_message[:100]}...")
        
        # Generate response using local model
        response_text = await local_model.generate_response(
            prompt=user_message,
            max_length=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p
        )
        
        processing_time = time.time() - start_time
        logger.info(f"✅ Generated response in {processing_time:.2f}s")
        
        return GenerateResponse(
            content=response_text,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating response: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Inference error: {str(e)}"
        )

@router.get("/model-info")
async def get_model_info():
    """
    Get thông tin model hiện tại
    """
    from app.main import local_model
    
    if not local_model:
        return {
            "status": "not_initialized",
            "message": "Local model not initialized"
        }
    
    return {
        "status": "ready" if local_model.is_available() else "not_ready",
        "info": local_model.get_model_info()
    }
