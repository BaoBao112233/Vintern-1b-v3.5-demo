"""
VLM (Vision Language Model) Client
Communicates with vLLM inference server
"""

import os
import base64
import logging
import requests
from typing import Optional, Dict
import numpy as np
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)


class VLMClient:
    """Client for vLLM inference API"""
    
    def __init__(
        self,
        api_url: str,
        timeout: int = 30,
        max_tokens: int = 512,
        temperature: float = 0.7
    ):
        """
        Initialize VLM client
        
        Args:
            api_url: vLLM API base URL
            timeout: Request timeout in seconds
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        """
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        logger.info("🧠 VLM Client initialized")
        logger.info(f"   API URL: {self.api_url}")
        logger.info(f"   Timeout: {self.timeout}s")
        logger.info(f"   Max tokens: {self.max_tokens}")
    
    def check_health(self) -> bool:
        """
        Check if vLLM server is healthy
        
        Returns:
            True if healthy
        """
        try:
            # Try health endpoint
            health_url = self.api_url.replace('/v1', '') + '/health'
            response = requests.get(health_url, timeout=5)
            
            if response.status_code == 200:
                logger.info("✅ vLLM server is healthy")
                return True
            
            # Fallback: try models endpoint
            models_url = f"{self.api_url}/models"
            response = requests.get(models_url, timeout=5)
            
            if response.status_code == 200:
                logger.info("✅ vLLM server is responding")
                return True
            
            logger.warning(f"⚠️  vLLM server returned {response.status_code}")
            return False
            
        except requests.exceptions.ConnectionError:
            logger.error("❌ Cannot connect to vLLM server")
            return False
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
    
    def _encode_image(self, image: np.ndarray) -> str:
        """
        Encode numpy image to base64 string
        
        Args:
            image: Image as numpy array (RGB)
        
        Returns:
            Base64 encoded image string
        """
        # Convert to PIL Image
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)
        
        pil_image = Image.fromarray(image)
        
        # Resize if too large (to save bandwidth)
        max_size = 1024
        if max(pil_image.size) > max_size:
            pil_image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Encode to base64
        buffer = BytesIO()
        pil_image.save(buffer, format='JPEG', quality=85)
        img_bytes = buffer.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        return f"data:image/jpeg;base64,{img_base64}"
    
    def analyze(
        self,
        image: np.ndarray,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Analyze image with VLM
        
        Args:
            image: Image as numpy array (RGB)
            prompt: Text prompt
            max_tokens: Override default max_tokens
            temperature: Override default temperature
        
        Returns:
            Model response text
        """
        try:
            # Encode image
            image_data = self._encode_image(image)
            
            # Prepare request
            payload = {
                "model": "Vintern-1B-v3_5",  # Will use whatever model is loaded
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_data}}
                        ]
                    }
                ],
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature
            }
            
            # Make request
            url = f"{self.api_url}/chat/completions"
            
            logger.info(f"🧠 Calling vLLM API: {url}")
            logger.info(f"   Prompt: {prompt[:80]}...")
            
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            if 'choices' in data and len(data['choices']) > 0:
                result = data['choices'][0]['message']['content']
                logger.info(f"✅ VLM response: {result[:100]}...")
                return result
            else:
                logger.error(f"❌ Unexpected response format: {data}")
                return "Error: Invalid response format"
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ Request timeout ({self.timeout}s)")
            return "Error: Request timeout"
        except requests.exceptions.ConnectionError:
            logger.error("❌ Cannot connect to vLLM server")
            return "Error: Connection failed"
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP error: {e}")
            logger.error(f"   Response: {e.response.text if e.response else 'N/A'}")
            return f"Error: HTTP {e.response.status_code if e.response else 'unknown'}"
        except Exception as e:
            logger.error(f"❌ VLM analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}"
    
    def analyze_text_only(self, prompt: str) -> str:
        """
        Text-only inference (no image)
        
        Args:
            prompt: Text prompt
        
        Returns:
            Model response
        """
        try:
            payload = {
                "model": "Vintern-1B-v3_5",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            url = f"{self.api_url}/chat/completions"
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            return data['choices'][0]['message']['content']
            
        except Exception as e:
            logger.error(f"❌ Text-only inference failed: {e}")
            return f"Error: {str(e)}"


# Test code
if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    
    logging.basicConfig(level=logging.INFO)
    
    # Get API URL
    api_url = os.getenv('VLLM_API_URL', 'http://localhost:8000/v1')
    
    logger.info("=" * 60)
    logger.info("VLM Client Test")
    logger.info("=" * 60)
    
    client = VLMClient(api_url=api_url)
    
    # Test health check
    logger.info("\n🏥 Testing health check...")
    is_healthy = client.check_health()
    
    if not is_healthy:
        logger.error("❌ vLLM server is not available")
        logger.info("\n💡 Make sure vLLM is running:")
        logger.info("   docker compose -f docker-compose.vllm.yml up vllm")
        sys.exit(1)
    
    # Test text-only inference
    logger.info("\n📝 Testing text-only inference...")
    text_response = client.analyze_text_only("Say hello in 5 words or less.")
    logger.info(f"Response: {text_response}")
    
    # Test image analysis
    logger.info("\n🖼️  Testing image analysis...")
    test_image = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
    image_response = client.analyze(
        test_image,
        "Describe this image in one sentence."
    )
    logger.info(f"Response: {image_response}")
    
    logger.info("\n✅ VLM Client test complete")
    logger.info("=" * 60)
