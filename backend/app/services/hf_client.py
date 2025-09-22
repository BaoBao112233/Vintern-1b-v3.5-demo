"""
Hugging Face Inference API Client
"""
import os
import asyncio
import logging
from typing import Optional, Dict, Any
import aiohttp
import base64
from io import BytesIO
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

class HuggingFaceClient:
    """Client for Hugging Face Inference API"""
    
    def __init__(self, token: Optional[str] = None, model_id: str = "5CD-AI/Vintern-1B-v3_5"):
        self.token = token
        self.model_id = model_id
        self.api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        self.headers = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self._ready = False
        self.timeout = aiohttp.ClientTimeout(total=30.0)
        
        if self.token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    async def initialize(self):
        """Initialize the client and check model availability"""
        logger.info(f"Initializing Hugging Face client for model: {self.model_id}")
        
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers=self.headers
        )
        
        try:
            # Test model availability
            await self._check_model_status()
            self._ready = True
            logger.info("Hugging Face client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Hugging Face client: {e}")
            self._ready = False
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
        self._ready = False
    
    def is_ready(self) -> bool:
        """Check if the client is ready"""
        return self._ready and self.session is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_id": self.model_id,
            "api_url": self.api_url,
            "has_token": bool(self.token)
        }
    
    async def _check_model_status(self):
        """Check if the model is available"""
        if not self.session:
            raise Exception("Session not initialized")
        
        try:
            async with self.session.get(f"https://huggingface.co/api/models/{self.model_id}") as response:
                if response.status == 200:
                    model_info = await response.json()
                    logger.info(f"Model {self.model_id} is available")
                    return model_info
                else:
                    raise Exception(f"Model not found: {response.status}")
        except Exception as e:
            logger.warning(f"Could not verify model status: {e}")
            # Continue anyway, some models might not have public API info
    
    async def predict(self, image: Image.Image) -> Dict[str, Any]:
        """
        Run inference on an image
        
        Args:
            image: PIL Image object
            
        Returns:
            Dict containing prediction results
        """
        if not self.is_ready():
            raise Exception("Client not ready")
        
        try:
            # Convert image to bytes
            img_buffer = BytesIO()
            image.save(img_buffer, format='JPEG', quality=85)
            img_bytes = img_buffer.getvalue()
            
            # Make inference request
            async with self.session.post(
                self.api_url,
                data=img_bytes,
                headers={"Content-Type": "application/octet-stream"}
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return await self._process_hf_response(result, image)
                elif response.status == 503:
                    error_text = await response.text()
                    if "loading" in error_text.lower():
                        raise Exception("Model is still loading, please try again later")
                    else:
                        raise Exception(f"Service unavailable: {error_text}")
                else:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")
                    
        except asyncio.TimeoutError:
            raise Exception("Request timeout - model inference took too long")
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            raise
    
    async def _process_hf_response(self, hf_result: Any, original_image: Image.Image) -> Dict[str, Any]:
        """
        Process Hugging Face API response and format for our application
        
        The exact format depends on what the Vintern-1B model returns.
        This is a generic implementation that handles common cases.
        """
        try:
            # Handle different response formats
            if isinstance(hf_result, list):
                # Object detection format
                processed_result = {
                    "detection_results": [],
                    "total_objects": len(hf_result),
                    "image_size": original_image.size
                }
                
                for detection in hf_result:
                    if isinstance(detection, dict):
                        processed_detection = {
                            "label": detection.get("label", "unknown"),
                            "confidence": detection.get("score", 0.0),
                            "bbox": detection.get("box", {}),
                        }
                        processed_result["detection_results"].append(processed_detection)
                
                # Create annotated image
                annotated_image = await self._create_annotated_image(
                    original_image, processed_result["detection_results"]
                )
                processed_result["annotated_image"] = annotated_image
                
                return processed_result
                
            elif isinstance(hf_result, dict):
                # Handle various dictionary formats
                if "generated_text" in hf_result:
                    # Text generation
                    return {
                        "type": "text_generation",
                        "generated_text": hf_result["generated_text"],
                        "image_size": original_image.size
                    }
                elif "predictions" in hf_result:
                    # Classification
                    return {
                        "type": "classification", 
                        "predictions": hf_result["predictions"],
                        "image_size": original_image.size
                    }
                else:
                    # Generic dictionary response
                    hf_result["image_size"] = original_image.size
                    return hf_result
            else:
                # Unknown format
                return {
                    "type": "unknown",
                    "raw_result": hf_result,
                    "image_size": original_image.size
                }
                
        except Exception as e:
            logger.error(f"Error processing HF response: {e}")
            return {
                "type": "error",
                "error": str(e),
                "raw_result": hf_result,
                "image_size": original_image.size
            }
    
    async def _create_annotated_image(self, image: Image.Image, detections: list) -> Image.Image:
        """Create annotated image with bounding boxes and labels"""
        try:
            from PIL import ImageDraw, ImageFont
            
            # Create a copy of the original image
            annotated = image.copy()
            draw = ImageDraw.Draw(annotated)
            
            # Try to load a font, fallback to default if not available
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except:
                font = ImageFont.load_default()
            
            # Draw bounding boxes and labels
            for detection in detections:
                bbox = detection.get("bbox", {})
                label = detection.get("label", "unknown")
                confidence = detection.get("confidence", 0.0)
                
                if bbox and all(k in bbox for k in ["xmin", "ymin", "xmax", "ymax"]):
                    # Draw bounding box
                    x1, y1, x2, y2 = bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"]
                    draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
                    
                    # Draw label with confidence
                    label_text = f"{label} ({confidence:.2f})"
                    draw.text((x1, y1 - 15), label_text, fill="red", font=font)
            
            return annotated
            
        except Exception as e:
            logger.error(f"Error creating annotated image: {e}")
            return image  # Return original image if annotation fails