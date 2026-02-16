"""
Vintern Vision Language Model Client
Supports multiple backends: HuggingFace API, Local VLLM, PC Inference Server
"""

import base64
import logging
import time
import requests
from typing import Dict, Any, Optional
from PIL import Image
import io

logger = logging.getLogger(__name__)


class VinternClient:
    """Client for Vintern VLM inference"""
    
    def __init__(
        self,
        hf_token: Optional[str] = None,
        vllm_url: Optional[str] = None,
        backend: str = "hf"  # "hf", "vllm", or "pc"
    ):
        """
        Args:
            hf_token: HuggingFace API token
            vllm_url: URL for VLLM or PC inference server
            backend: Which backend to use
        """
        self.hf_token = hf_token
        self.vllm_url = vllm_url
        self.backend = backend
        
        # Try to import HuggingFace client
        try:
            from huggingface_hub import InferenceClient
            self.hf_client = InferenceClient(token=hf_token) if hf_token else None
        except ImportError:
            logger.warning("huggingface_hub not installed")
            self.hf_client = None
    
    def encode_image_base64(self, image_bytes: bytes) -> str:
        """Encode image to base64 data URL"""
        b64 = base64.b64encode(image_bytes).decode('utf-8')
        return f"data:image/jpeg;base64,{b64}"
    
    def analyze_image_hf(
        self,
        image_bytes: bytes,
        prompt: str,
        max_tokens: int = 256
    ) -> Dict[str, Any]:
        """Analyze using HuggingFace Inference API"""
        start_time = time.time()
        
        try:
            if not self.hf_client:
                return {
                    "success": False,
                    "error": "HuggingFace client not available"
                }
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Try visual question answering
            try:
                response = self.hf_client.visual_question_answering(
                    image=image,
                    question=prompt,
                    model="5CD-AI/Vintern-1B-v3_5"
                )
                
                latency_ms = (time.time() - start_time) * 1000
                
                # Parse response
                if isinstance(response, list) and len(response) > 0:
                    answer = response[0].get('answer', str(response))
                elif isinstance(response, dict):
                    answer = response.get('answer', str(response))
                else:
                    answer = str(response)
                
                return {
                    "success": True,
                    "response": answer,
                    "latency_ms": latency_ms
                }
                
            except Exception as e:
                logger.warning(f"HF VQA failed: {e}")
                
                # Try chat completion as fallback
                try:
                    messages = [
                        {
                            "role": "user",
                            "content": [
                                {"type": "image"},
                                {"type": "text", "text": prompt}
                            ]
                        }
                    ]
                    
                    response = self.hf_client.chat_completion(
                        messages=messages,
                        model="5CD-AI/Vintern-1B-v3_5",
                        max_tokens=max_tokens
                    )
                    
                    latency_ms = (time.time() - start_time) * 1000
                    
                    answer = response.choices[0].message.content if hasattr(response, 'choices') else str(response)
                    
                    return {
                        "success": True,
                        "response": answer,
                        "latency_ms": latency_ms
                    }
                    
                except Exception as e2:
                    logger.error(f"HF chat completion also failed: {e2}")
                    return {
                        "success": False,
                        "error": f"Both HF methods failed: {e}, {e2}",
                        "latency_ms": (time.time() - start_time) * 1000
                    }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "latency_ms": (time.time() - start_time) * 1000
            }
    
    def analyze_image_vllm(
        self,
        image_bytes: bytes,
        prompt: str,
        max_tokens: int = 256
    ) -> Dict[str, Any]:
        """Analyze using local VLLM or PC inference server"""
        start_time = time.time()
        
        try:
            if not self.vllm_url:
                return {
                    "success": False,
                    "error": "VLLM URL not configured"
                }
            
            image_url = self.encode_image_base64(image_bytes)
            
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": image_url}},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            response = requests.post(
                f"{self.vllm_url}/v1/chat/completions",
                json=payload,
                timeout=30
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                answer = result["choices"][0]["message"]["content"]
                
                return {
                    "success": True,
                    "response": answer,
                    "latency_ms": latency_ms,
                    "tokens_used": result.get("usage", {}).get("total_tokens", 0)
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "latency_ms": latency_ms
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "latency_ms": (time.time() - start_time) * 1000
            }
    
    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str = "Describe what you see in this image.",
        max_tokens: int = 512
    ) -> Dict[str, Any]:
        """
        Analyze image using configured backend
        
        Returns:
            Dict with 'success', 'response', 'error', 'latency_ms'
        """
        if self.backend == "hf":
            return self.analyze_image_hf(image_bytes, prompt, max_tokens)
        elif self.backend in ["vllm", "pc"]:
            return self.analyze_image_vllm(image_bytes, prompt, max_tokens)
        else:
            return {
                "success": False,
                "error": f"Unknown backend: {self.backend}"
            }
