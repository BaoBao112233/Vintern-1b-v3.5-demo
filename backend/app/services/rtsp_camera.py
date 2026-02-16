"""
RTSP Camera Service for Dahua Cameras
Captures frames from RTSP streams
"""

import cv2
import logging
from typing import Optional, Tuple
import time

logger = logging.getLogger(__name__)


class RTSPCamera:
    """RTSP Camera client for Dahua cameras"""
    
    def __init__(
        self,
        camera_url: str,
        camera_name: str = "Camera",
        reconnect_delay: int = 5
    ):
        """
        Args:
            camera_url: Full RTSP URL
            camera_name: Name for logging
            reconnect_delay: Seconds to wait before reconnecting
        """
        self.camera_url = camera_url
        self.camera_name = camera_name
        self.reconnect_delay = reconnect_delay
        self.cap = None
        self.is_connected = False
        
    def connect(self) -> bool:
        """Connect to RTSP stream"""
        try:
            logger.info(f"Connecting to {self.camera_name}: {self.camera_url}")
            
            self.cap = cv2.VideoCapture(self.camera_url)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce lag
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open {self.camera_name}")
                return False
            
            # Test read
            ret, frame = self.cap.read()
            if not ret:
                logger.error(f"Failed to read from {self.camera_name}")
                return False
            
            self.is_connected = True
            logger.info(f"✅ Connected to {self.camera_name} - Frame: {frame.shape}")
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def capture_frame(self) -> Optional[Tuple[bool, bytes]]:
        """
        Capture a frame and return as JPEG bytes
        
        Returns:
            (success, jpeg_bytes) or None if failed
        """
        try:
            # Reconnect if needed
            if not self.is_connected or not self.cap or not self.cap.isOpened():
                if not self.connect():
                    return None
            
            ret, frame = self.cap.read()
            if not ret:
                logger.warning(f"{self.camera_name}: Frame read failed, reconnecting...")
                self.is_connected = False
                self.cap.release()
                return None
            
            # Encode to JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ret:
                logger.error(f"{self.camera_name}: Failed to encode frame")
                return None
            
            return True, buffer.tobytes()
            
        except Exception as e:
            logger.error(f"{self.camera_name}: Capture error: {e}")
            self.is_connected = False
            return None
    
    def release(self):
        """Release camera resources"""
        if self.cap:
            self.cap.release()
            self.is_connected = False
            logger.info(f"{self.camera_name}: Released")
