"""
Detection Integration Service
Integrates backend with detection-service for object detection
"""

import os
import logging
import httpx
import base64
import numpy as np
import cv2
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class DetectionClient:
    """Client for detection service"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("DETECTION_SERVICE_URL", "http://localhost:8001")
        self.client = httpx.AsyncClient(timeout=30.0)
        self._ready = False
    
    async def initialize(self):
        """Initialize and check connection"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                self._ready = data.get("detector_ready", False)
                logger.info(f"✅ Detection service connected: {self.base_url}")
                return True
        except Exception as e:
            logger.error(f"Failed to connect to detection service: {e}")
        return False
    
    def is_ready(self) -> bool:
        """Check if detection service is ready"""
        return self._ready
    
    async def detect_objects(
        self,
        image: np.ndarray,
        draw_boxes: bool = False
    ) -> Dict[str, Any]:
        """
        Detect objects in image
        
        Args:
            image: numpy array (BGR format)
            draw_boxes: Whether to return image with bounding boxes
            
        Returns:
            Detection results
        """
        try:
            # Encode image to base64
            _, buffer = cv2.imencode('.jpg', image)
            image_b64 = base64.b64encode(buffer).decode('utf-8')
            
            # Send request
            response = await self.client.post(
                f"{self.base_url}/api/detect",
                json={
                    "image_base64": image_b64,
                    "draw_boxes": draw_boxes
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Detection failed: {response.status_code}")
                return {"success": False, "detections": [], "summary": "Detection failed"}
                
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return {"success": False, "detections": [], "summary": f"Error: {str(e)}"}
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.client.aclose()


# Global instance
_detection_client: Optional[DetectionClient] = None


async def get_detection_client() -> DetectionClient:
    """Get or create detection client"""
    global _detection_client
    
    if _detection_client is None:
        _detection_client = DetectionClient()
        await _detection_client.initialize()
    
    return _detection_client
