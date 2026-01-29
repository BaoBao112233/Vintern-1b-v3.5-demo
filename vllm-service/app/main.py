"""
VLLM Service - FastAPI Application
Orange Pi RV 2 - Vision Language Model
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.analyze import router as analyze_router
from app.models.vllm import get_vllm

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup"""
    logger.info("🚀 Starting VLLM Service...")
    logger.info(f"📍 Service IP: {os.getenv('SERVICE_IP', '192.168.100.20')}")
    
    # Initialize VLLM
    vllm = await get_vllm()
    
    if vllm.is_ready():
        logger.info("✅ VLLM Service ready!")
        
        # Log memory usage
        mem = vllm.get_memory_usage()
        logger.info(f"💾 Memory: RSS={mem['rss']}, VMS={mem['vms']}")
    else:
        logger.error("❌ VLLM failed to initialize")
    
    yield
    
    logger.info("👋 Shutting down VLLM Service...")


# Create app
app = FastAPI(
    title="VLLM Service",
    description="Vision Language Model Service on Orange Pi RV 2",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analyze_router, prefix="/api", tags=["analysis"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "VLLM Service",
        "status": "running",
        "hardware": "Orange Pi RV 2 (4GB RAM)",
        "model": "Vintern-1B-v3.5",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check"""
    vllm = await get_vllm()
    
    health_status = {
        "status": "healthy",
        "vllm_ready": vllm.is_ready() if vllm else False,
        "service_ip": os.getenv("SERVICE_IP", "192.168.100.20"),
        "detection_service": os.getenv("DETECTION_SERVICE_URL", "http://192.168.100.10:8001")
    }
    
    if vllm and vllm.is_ready():
        health_status.update({
            "model_info": vllm.get_model_info(),
            "memory_usage": vllm.get_memory_usage()
        })
    
    return health_status


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8002))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
