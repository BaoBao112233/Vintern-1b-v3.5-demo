"""
Local Model Runner using GGML/llama.cpp
"""
import os
import asyncio
import logging
import subprocess
import json
import tempfile
from typing import Optional, Dict, Any
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

class LocalRunner:
    """Local model runner using GGML/llama.cpp or similar"""
    
    def __init__(self, model_path: str = "/models"):
        self.model_path = model_path
        self.model_file = None
        self.executable_path = None
        self._ready = False
        self.model_config = {}
        
    async def initialize(self):
        """Initialize the local model runner"""
        logger.info(f"Initializing local model runner from: {self.model_path}")
        
        try:
            # Look for model files
            self.model_file = await self._find_model_file()
            if not self.model_file:
                raise Exception(f"No model file found in {self.model_path}")
            
            # Look for executable
            self.executable_path = await self._find_executable()
            if not self.executable_path:
                raise Exception("No inference executable found")
            
            # Load model configuration if available
            config_file = os.path.join(self.model_path, "config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    self.model_config = json.load(f)
            
            # Test model loading
            await self._test_model()
            
            self._ready = True
            logger.info("Local model runner initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize local runner: {e}")
            self._ready = False
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        self._ready = False
    
    def is_ready(self) -> bool:
        """Check if the runner is ready"""
        return self._ready
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_path": self.model_path,
            "model_file": self.model_file,
            "executable_path": self.executable_path,
            "config": self.model_config
        }
    
    async def _find_model_file(self) -> Optional[str]:
        """Find model file in the model directory"""
        if not os.path.exists(self.model_path):
            return None
        
        # Look for common model file extensions
        model_extensions = ['.gguf', '.ggml', '.bin', '.safetensors']
        
        for file in os.listdir(self.model_path):
            for ext in model_extensions:
                if file.endswith(ext):
                    full_path = os.path.join(self.model_path, file)
                    logger.info(f"Found model file: {full_path}")
                    return full_path
        
        return None
    
    async def _find_executable(self) -> Optional[str]:
        """Find inference executable"""
        # Common locations for llama.cpp or similar executables
        common_paths = [
            "/usr/local/bin/llama-server",
            "/usr/local/bin/main",
            "/app/llama.cpp/main",
            "/app/llama.cpp/llama-server",
            os.path.join(self.model_path, "main"),
            os.path.join(self.model_path, "llama-server"),
        ]
        
        for path in common_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                logger.info(f"Found executable: {path}")
                return path
        
        # Try to find in PATH
        try:
            result = subprocess.run(
                ["which", "llama-server"], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                path = result.stdout.strip()
                logger.info(f"Found executable in PATH: {path}")
                return path
        except:
            pass
        
        return None
    
    async def _test_model(self):
        """Test if the model can be loaded"""
        logger.info("Testing model loading...")
        
        # This is a placeholder test
        # In a real implementation, you would test loading the model
        # For now, we just check if files exist
        if not os.path.exists(self.model_file):
            raise Exception(f"Model file not found: {self.model_file}")
        
        if not os.path.exists(self.executable_path):
            raise Exception(f"Executable not found: {self.executable_path}")
        
        logger.info("Model test passed")
    
    async def predict(self, image: Image.Image) -> Dict[str, Any]:
        """
        Run inference on an image using local model
        
        Args:
            image: PIL Image object
            
        Returns:
            Dict containing prediction results
        """
        if not self.is_ready():
            raise Exception("Local runner not ready")
        
        try:
            # Save image to temporary file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                image.save(temp_file.name, 'JPEG')
                temp_image_path = temp_file.name
            
            try:
                # Run inference
                result = await self._run_inference(temp_image_path)
                
                # Process result
                processed_result = await self._process_local_result(result, image)
                
                return processed_result
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_image_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Local prediction error: {e}")
            raise
    
    async def _run_inference(self, image_path: str) -> str:
        """Run the actual inference command"""
        
        # This is a placeholder implementation
        # The actual command depends on how the GGML model is set up
        
        # Example command for llama.cpp with vision capabilities
        cmd = [
            self.executable_path,
            "-m", self.model_file,
            "--image", image_path,
            "--temp", "0.1",
            "--n_predict", "256",
        ]
        
        # Add additional parameters from config
        if "n_ctx" in self.model_config:
            cmd.extend(["--ctx_size", str(self.model_config["n_ctx"])])
        
        if "n_threads" in self.model_config:
            cmd.extend(["--threads", str(self.model_config["n_threads"])])
        
        logger.info(f"Running inference command: {' '.join(cmd)}")
        
        try:
            # Run the command with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=30.0
            )
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise Exception(f"Inference failed: {error_msg}")
            
            return stdout.decode()
            
        except asyncio.TimeoutError:
            raise Exception("Inference timeout")
        except Exception as e:
            raise Exception(f"Inference execution error: {e}")
    
    async def _process_local_result(self, result_text: str, original_image: Image.Image) -> Dict[str, Any]:
        """Process the result from local inference"""
        
        try:
            # Try to parse as JSON first
            try:
                parsed_result = json.loads(result_text)
                parsed_result["image_size"] = original_image.size
                parsed_result["type"] = "structured"
                return parsed_result
            except json.JSONDecodeError:
                pass
            
            # If not JSON, treat as text description
            return {
                "type": "text_description",
                "description": result_text.strip(),
                "image_size": original_image.size,
                "raw_output": result_text
            }
            
        except Exception as e:
            logger.error(f"Error processing local result: {e}")
            return {
                "type": "error",
                "error": str(e),
                "raw_output": result_text,
                "image_size": original_image.size
            }