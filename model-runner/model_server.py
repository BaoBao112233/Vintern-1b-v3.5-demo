"""
Local Model Server for Vintern-1B using GGML/llama.cpp
Provides HTTP API for local model inference
"""

import os
import sys
import asyncio
import logging
import subprocess
import json
import tempfile
import signal
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from PIL import Image
import aiofiles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/logs/model_server.log')
    ]
)
logger = logging.getLogger(__name__)

class InferenceRequest(BaseModel):
    """Request model for inference"""
    image_path: str
    prompt: Optional[str] = None
    max_tokens: int = 256
    temperature: float = 0.1

class InferenceResponse(BaseModel):
    """Response model for inference"""
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    processing_time: float = 0.0

class ModelServer:
    """Local model server using llama.cpp"""
    
    def __init__(self):
        self.model_path = os.getenv("MODEL_PATH", "/models")
        self.llama_cpp_path = os.getenv("LLAMA_CPP_PATH", "/app/llama.cpp")
        self.model_file = None
        self.executable_path = None
        self.is_ready = False
        self.model_config = {}
        
    async def initialize(self):
        """Initialize the model server"""
        logger.info("Initializing Local Model Server...")
        
        try:
            # Find model file
            self.model_file = self._find_model_file()
            if not self.model_file:
                logger.warning(f"No model file found in {self.model_path}")
                logger.info("Model server will be available but inference will fail until a model is provided")
                return
            
            # Find executable
            self.executable_path = self._find_executable()
            if not self.executable_path:
                raise Exception("llama.cpp executable not found")
            
            # Load model configuration
            self._load_model_config()
            
            # Test model loading
            await self._test_model()
            
            self.is_ready = True
            logger.info("Model server initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize model server: {e}")
            self.is_ready = False
    
    def _find_model_file(self) -> Optional[str]:
        """Find model file in the model directory"""
        if not os.path.exists(self.model_path):
            return None
        
        # Look for model files
        extensions = ['.gguf', '.ggml', '.bin']
        
        for file in os.listdir(self.model_path):
            for ext in extensions:
                if file.endswith(ext):
                    full_path = os.path.join(self.model_path, file)
                    logger.info(f"Found model file: {full_path}")
                    return full_path
        
        return None
    
    def _find_executable(self) -> Optional[str]:
        """Find llama.cpp executable"""
        # Try different executable names
        executables = ['main', 'llama-server', 'llama-cli']
        
        for exe in executables:
            exe_path = os.path.join(self.llama_cpp_path, exe)
            if os.path.exists(exe_path) and os.access(exe_path, os.X_OK):
                logger.info(f"Found executable: {exe_path}")
                return exe_path
        
        return None
    
    def _load_model_config(self):
        """Load model configuration if available"""
        config_file = os.path.join(self.model_path, "config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    self.model_config = json.load(f)
                logger.info(f"Loaded model config: {self.model_config}")
            except Exception as e:
                logger.warning(f"Failed to load model config: {e}")
                self.model_config = {}
        else:
            # Default configuration
            self.model_config = {
                "n_ctx": 2048,
                "n_threads": int(os.getenv("INFERENCE_THREADS", "4")),
                "temperature": 0.1,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
    
    async def _test_model(self):
        """Test model loading"""
        if not self.model_file or not self.executable_path:
            return
        
        logger.info("Testing model loading...")
        
        # Simple test command
        cmd = [
            self.executable_path,
            "-m", self.model_file,
            "--n_predict", "1",
            "--temp", "0.1",
            "--prompt", "Hello",
            "--verbose"
        ]
        
        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                result.communicate(), 
                timeout=30.0
            )
            
            if result.returncode == 0:
                logger.info("Model test passed")
            else:
                logger.warning(f"Model test failed: {stderr.decode()}")
                
        except asyncio.TimeoutError:
            logger.warning("Model test timed out")
        except Exception as e:
            logger.warning(f"Model test error: {e}")
    
    async def infer(self, image_path: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """Run inference on an image"""
        if not self.is_ready or not self.model_file:
            raise HTTPException(
                status_code=503, 
                detail="Model not ready or model file not found"
            )
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Prepare inference command
            cmd = self._build_inference_command(image_path, prompt)
            
            logger.info(f"Running inference: {' '.join(cmd[:5])}...")
            
            # Run inference
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=60.0  # 1 minute timeout
            )
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"Inference failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "processing_time": processing_time
                }
            
            # Process output
            output = stdout.decode().strip()
            result = self._process_output(output)
            
            return {
                "success": True,
                "result": result,
                "processing_time": processing_time
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Inference timeout",
                "processing_time": asyncio.get_event_loop().time() - start_time
            }
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": asyncio.get_event_loop().time() - start_time
            }
    
    def _build_inference_command(self, image_path: str, prompt: Optional[str]) -> list:
        """Build inference command for llama.cpp"""
        cmd = [
            self.executable_path,
            "-m", self.model_file,
            "--image", image_path,
        ]
        
        # Add configuration parameters
        cmd.extend([
            "--ctx_size", str(self.model_config.get("n_ctx", 2048)),
            "--threads", str(self.model_config.get("n_threads", 4)),
            "--temp", str(self.model_config.get("temperature", 0.1)),
            "--top_p", str(self.model_config.get("top_p", 0.9)),
            "--repeat_penalty", str(self.model_config.get("repeat_penalty", 1.1)),
            "--n_predict", "256"
        ])
        
        # Add prompt if provided
        if prompt:
            cmd.extend(["--prompt", prompt])
        else:
            cmd.extend(["--prompt", "Describe what you see in this image in detail."])
        
        return cmd
    
    def _process_output(self, output: str) -> str:
        """Process the raw output from llama.cpp"""
        # llama.cpp outputs include metadata, we need to extract just the generated text
        lines = output.split('\n')
        
        # Look for the actual generated text
        # This might need adjustment based on the actual output format
        generated_lines = []
        capture = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip metadata and system messages
            if line.startswith('llama_') or line.startswith('system_info') or line.startswith('main:'):
                continue
            
            # Look for the prompt echo end
            if 'Describe what you see' in line or capture:
                capture = True
                if 'Describe what you see' not in line:
                    generated_lines.append(line)
        
        result = ' '.join(generated_lines).strip()
        
        # Fallback: if we couldn't parse properly, return the last substantial line
        if not result:
            substantial_lines = [l for l in lines if l.strip() and not l.startswith('llama_') and not l.startswith('main:')]
            if substantial_lines:
                result = substantial_lines[-1].strip()
        
        return result or "Unable to generate description"
    
    def get_status(self) -> Dict[str, Any]:
        """Get server status"""
        return {
            "ready": self.is_ready,
            "model_path": self.model_path,
            "model_file": self.model_file,
            "executable_path": self.executable_path,
            "config": self.model_config
        }

# Global model server instance
model_server = ModelServer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await model_server.initialize()
    yield
    # Shutdown
    logger.info("Shutting down model server...")

# Create FastAPI app
app = FastAPI(
    title="Vintern-1B Local Model Server",
    description="Local inference server using GGML/llama.cpp",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = model_server.get_status()
    return {
        "status": "healthy" if status["ready"] else "not_ready",
        "model_ready": status["ready"],
        "details": status
    }

@app.post("/infer", response_model=InferenceResponse)
async def infer_endpoint(request: InferenceRequest):
    """Inference endpoint"""
    result = await model_server.infer(
        image_path=request.image_path,
        prompt=request.prompt
    )
    
    return InferenceResponse(**result)

@app.post("/infer/upload")
async def infer_upload(
    file: UploadFile = File(...),
    prompt: Optional[str] = None
):
    """Inference with file upload"""
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name
    
    try:
        # Run inference
        result = await model_server.infer(temp_path, prompt)
        return result
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_path)
        except:
            pass

@app.get("/models")
async def list_models():
    """List available models"""
    models = []
    
    if os.path.exists(model_server.model_path):
        for file in os.listdir(model_server.model_path):
            if file.endswith(('.gguf', '.ggml', '.bin')):
                file_path = os.path.join(model_server.model_path, file)
                file_size = os.path.getsize(file_path)
                models.append({
                    "name": file,
                    "path": file_path,
                    "size": file_size,
                    "is_current": file_path == model_server.model_file
                })
    
    return {"models": models}

if __name__ == "__main__":
    # Handle signals gracefully
    def signal_handler(sig, frame):
        logger.info("Received signal, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run server
    uvicorn.run(
        "model_server:app",
        host="0.0.0.0",
        port=8001,
        log_level="info",
        access_log=True
    )