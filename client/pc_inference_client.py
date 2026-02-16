#!/usr/bin/env python3
"""
PC Inference Client for Raspberry Pi

Client library để Raspberry Pi gửi request sang PC inference server
"""

import base64
import json
import logging
import time
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Union

import requests
from PIL import Image

logger = logging.getLogger(__name__)


class PCInferenceClient:
    """Client để giao tiếp với PC inference server từ Raspberry Pi"""
    
    def __init__(
        self,
        pc_host: str = "192.168.1.100",
        pc_port: int = 8080,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Args:
            pc_host: IP address của PC trên LAN
            pc_port: Port của PC inference server (default: 8080)
            timeout: Request timeout (seconds)
            max_retries: Số lần retry khi fail
            retry_delay: Delay giữa các retry (seconds)
        """
        self.base_url = f"http://{pc_host}:{pc_port}"
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._session = requests.Session()
        
        logger.info(f"Initialized PC Inference Client: {self.base_url}")
    
    def health_check(self) -> bool:
        """
        Kiểm tra xem PC server có sẵn sàng không
        
        Returns:
            True nếu server healthy, False nếu không
        """
        try:
            response = self._session.get(
                f"{self.base_url}/health",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                is_healthy = data.get("status") == "ok"
                logger.info(f"Health check: {'OK' if is_healthy else 'FAILED'}")
                return is_healthy
            else:
                logger.warning(f"Health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return False
    
    def encode_image(
        self,
        image: Union[str, Path, Image.Image, bytes],
        max_size: Optional[tuple] = (1024, 1024),
        quality: int = 85
    ) -> str:
        """
        Encode image thành base64 URL format
        
        Args:
            image: Path to image, PIL Image, hoặc bytes
            max_size: Max (width, height) để resize, None = không resize
            quality: JPEG quality (1-100)
        
        Returns:
            Data URL string (data:image/jpeg;base64,...)
        """
        # Load image
        if isinstance(image, (str, Path)):
            img = Image.open(image)
        elif isinstance(image, bytes):
            img = Image.open(BytesIO(image))
        elif isinstance(image, Image.Image):
            img = image
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")
        
        # Convert RGBA to RGB if needed
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if needed
        if max_size and (img.width > max_size[0] or img.height > max_size[1]):
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            logger.debug(f"Resized image to {img.size}")
        
        # Encode to base64
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        img_bytes = buffer.getvalue()
        b64_data = base64.b64encode(img_bytes).decode('utf-8')
        
        data_url = f"data:image/jpeg;base64,{b64_data}"
        logger.debug(f"Encoded image: {len(b64_data)} bytes")
        
        return data_url
    
    def chat_completion(
        self,
        image: Union[str, Path, Image.Image, bytes],
        prompt: str,
        max_tokens: int = 200,
        temperature: float = 0.1,
        stream: bool = False
    ) -> Dict:
        """
        Gửi image + prompt sang PC để inference
        
        Args:
            image: Image để analyze
            prompt: Text prompt (tiếng Việt hoặc English)
            max_tokens: Max số tokens trong response
            temperature: Sampling temperature (0=deterministic, 1=creative)
            stream: Có stream response không (chưa support)
        
        Returns:
            Dict với keys: 'content', 'usage', 'error' (nếu có)
        """
        start_time = time.time()
        
        # Encode image
        try:
            image_url = self.encode_image(image)
        except Exception as e:
            logger.error(f"Failed to encode image: {e}")
            return {"error": f"Image encoding failed: {e}"}
        
        # Prepare request
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
            "temperature": temperature,
            "stream": stream
        }
        
        # Send request with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Sending request to PC (attempt {attempt + 1}/{self.max_retries})")
                
                response = self._session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                        usage = result.get("usage", {})
                        
                        elapsed = time.time() - start_time
                        logger.info(f"Inference success in {elapsed:.2f}s")
                        
                        return {
                            "content": content,
                            "usage": usage,
                            "elapsed_time": elapsed
                        }
                    else:
                        last_error = f"Invalid response format: {result}"
                        logger.warning(last_error)
                else:
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    logger.warning(last_error)
                    
            except requests.exceptions.Timeout:
                last_error = "Request timeout"
                logger.warning(f"Request timeout (attempt {attempt + 1})")
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {e}"
                logger.warning(f"Connection error (attempt {attempt + 1}): {e}")
            except Exception as e:
                last_error = f"Unexpected error: {e}"
                logger.error(f"Unexpected error (attempt {attempt + 1}): {e}")
            
            # Delay before retry
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)
        
        # All retries failed
        elapsed = time.time() - start_time
        logger.error(f"All retries failed after {elapsed:.2f}s")
        return {
            "error": last_error,
            "elapsed_time": elapsed
        }
    
    def analyze_detections(
        self,
        image: Union[str, Path, Image.Image, bytes],
        detections: List[Dict],
        custom_prompt: Optional[str] = None
    ) -> Dict:
        """
        Gửi image với detected objects để VLM analyze
        
        Args:
            image: Image đã detect
            detections: List các detected objects
                [{"class": "person", "confidence": 0.95, "bbox": [x,y,w,h]}, ...]
            custom_prompt: Custom prompt, nếu None sẽ dùng default
        
        Returns:
            Dict response từ PC
        """
        # Build prompt với detection info
        if custom_prompt:
            prompt = custom_prompt
        else:
            if detections:
                objects_str = ", ".join([
                    f"{d['class']} ({d['confidence']:.0%})" 
                    for d in detections
                ])
                prompt = (
                    f"Tôi đã phát hiện các vật thể sau: {objects_str}. "
                    f"Hãy mô tả chi tiết về các vật thể này và những gì đang xảy ra trong ảnh."
                )
            else:
                prompt = "Mô tả những gì bạn thấy trong ảnh này."
        
        return self.chat_completion(image, prompt)
    
    def close(self):
        """Đóng session"""
        self._session.close()
        logger.info("Client session closed")


# Example usage
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # PC IP address - THAY ĐỔI CHỖ NÀY!
    PC_IP = "192.168.1.100"  # <-- Sửa thành IP của PC
    
    client = PCInferenceClient(pc_host=PC_IP)
    
    # Test 1: Health check
    print("\n=== Test 1: Health Check ===")
    if client.health_check():
        print("✅ PC server is ready!")
    else:
        print("❌ PC server is not available")
        sys.exit(1)
    
    # Test 2: Inference (nếu có image path)
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        prompt = sys.argv[2] if len(sys.argv) > 2 else "Mô tả chi tiết những gì bạn thấy trong ảnh này."
        
        print(f"\n=== Test 2: Inference ===")
        print(f"Image: {image_path}")
        print(f"Prompt: {prompt}")
        
        result = client.chat_completion(image_path, prompt)
        
        if "error" in result:
            print(f"\n❌ Error: {result['error']}")
        else:
            print(f"\n✅ Response:")
            print(result['content'])
            print(f"\nTime: {result['elapsed_time']:.2f}s")
            if 'usage' in result:
                print(f"Tokens: {result['usage']}")
    else:
        print("\n⚠️ Không có ảnh để test inference")
        print("Usage: python pc_inference_client.py <image_path> [prompt]")
    
    client.close()
