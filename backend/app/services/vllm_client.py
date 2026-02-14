"""
VLLM Client - Kết nối đến VLLM Service trên Orange Pi
"""
import os
import logging
from typing import Optional, Dict, Any, List
import aiohttp
import asyncio

logger = logging.getLogger(__name__)


class VLLMClient:
    """Client kết nối đến VLLM Service (Orange Pi)"""
    
    def __init__(
        self,
        vllm_url: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize VLLM client
        
        Args:
            vllm_url: URL của VLLM service (e.g., http://192.168.1.16:8002)
            timeout: Timeout cho request (seconds)
        """
        self.vllm_url = vllm_url or os.getenv("VLLM_SERVICE_URL", "http://192.168.1.16:8002")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
        self._ready = False
        
        logger.info(f"Initializing VLLM client with URL: {self.vllm_url}")
    
    async def initialize(self):
        """Initialize the client"""
        try:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
            
            # Test connection
            await self._check_health()
            self._ready = True
            logger.info("✅ VLLM client initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize VLLM client: {e}")
            logger.warning("Continuing without VLLM service (detection only mode)")
            self._ready = False
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
        self._ready = False
    
    def is_available(self) -> bool:
        """Check if VLLM service is available"""
        return self._ready and self.session is not None
    
    async def _check_health(self):
        """Check VLLM service health"""
        if not self.session:
            raise Exception("Session not initialized")
        
        try:
            async with self.session.get(f"{self.vllm_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"VLLM service health check: {data}")
                    return True
                else:
                    raise Exception(f"Health check failed: {response.status}")
        except Exception as e:
            logger.error(f"Health check error: {e}")
            raise
    
    async def analyze(
        self,
        image_description: str,
        detected_objects: List[Dict[str, Any]],
        question: str = "Mô tả những gì bạn thấy trong ảnh"
    ) -> Dict[str, Any]:
        """
        Gửi request phân tích đến VLLM service
        
        Args:
            image_description: Mô tả ảnh
            detected_objects: Danh sách objects được detect
            question: Câu hỏi của người dùng
        
        Returns:
            Dict chứa response từ VLLM service
        """
        if not self.is_available():
            return {
                "error": "VLLM service not available",
                "response": f"Detection only: Phát hiện được {len(detected_objects)} vật thể trong ảnh."
            }
        
        try:
            payload = {
                "image_description": image_description,
                "detected_objects": detected_objects,
                "question": question
            }
            
            logger.info(f"Sending request to VLLM service: {question}")
            
            async with self.session.post(
                f"{self.vllm_url}/api/analyze",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"VLLM response received: {len(data.get('response', ''))} chars")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"VLLM request failed: {response.status} - {error_text}")
                    return {
                        "error": f"Request failed: {response.status}",
                        "response": f"Detection only: Phát hiện {len(detected_objects)} vật thể."
                    }
        
        except asyncio.TimeoutError:
            logger.error("VLLM request timeout")
            return {
                "error": "Request timeout",
                "response": f"Detection only: Phát hiện {len(detected_objects)} vật thể."
            }
        
        except Exception as e:
            logger.error(f"VLLM request error: {e}")
            return {
                "error": str(e),
                "response": f"Detection only: Phát hiện {len(detected_objects)} vật thể."
            }
    
    async def chat(
        self,
        message: str,
        context: Optional[str] = None,
        detected_objects: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Chat với VLLM service
        
        Args:
            message: Tin nhắn từ user
            context: Context bổ sung
            detected_objects: Objects được detect
        
        Returns:
            Response từ VLLM
        """
        if not self.is_available():
            return f"VLLM service không khả dụng. Chỉ có thể dùng detection service."
        
        try:
            payload = {
                "message": message,
                "context": context,
                "detected_objects": detected_objects or []
            }
            
            async with self.session.post(
                f"{self.vllm_url}/api/chat",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("response", "Không có phản hồi")
                else:
                    error_text = await response.text()
                    logger.error(f"Chat request failed: {response.status} - {error_text}")
                    return f"Lỗi: Không thể kết nối VLLM service"
        
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"Lỗi: {str(e)}"
    
    def get_info(self) -> Dict[str, Any]:
        """Get VLLM client info"""
        return {
            "vllm_url": self.vllm_url,
            "available": self.is_available(),
            "status": "ready" if self._ready else "not_ready"
        }


# Global instance
_vllm_client: Optional[VLLMClient] = None


async def get_vllm_client() -> VLLMClient:
    """Get or create VLLM client instance"""
    global _vllm_client
    
    if _vllm_client is None:
        _vllm_client = VLLMClient()
        await _vllm_client.initialize()
    
    return _vllm_client


async def initialize_vllm_client() -> VLLMClient:
    """Initialize VLLM client on startup"""
    return await get_vllm_client()
