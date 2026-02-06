"""
RTSP Camera Manager for multiple IP cameras
Handles RTSP streams and frame extraction
"""

import cv2
import logging
import asyncio
import numpy as np
from typing import Optional, Dict, Any
from dataclasses import dataclass
import threading
from queue import Queue

logger = logging.getLogger(__name__)


@dataclass
class CameraConfig:
    """Camera configuration"""
    id: str
    name: str
    rtsp_url: str
    username: str
    password: str
    ip: str
    width: int = 640
    height: int = 480
    fps: int = 5


class RTSPCamera:
    """Single RTSP camera handler"""
    
    def __init__(self, config: CameraConfig):
        self.config = config
        self.capture: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.frame_queue = Queue(maxsize=2)  # Keep only latest 2 frames
        self.thread: Optional[threading.Thread] = None
        self.last_frame: Optional[np.ndarray] = None
        self.error_count = 0
        self.max_errors = 10
        
    def start(self) -> bool:
        """Start camera capture"""
        try:
            logger.info(f"Starting camera {self.config.name} ({self.config.ip})")
            
            # Build RTSP URL with credentials
            rtsp_url = self.config.rtsp_url.format(
                username=self.config.username,
                password=self.config.password,
                ip=self.config.ip
            )
            
            # Open video capture with RTSP transport TCP
            self.capture = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
            
            if not self.capture.isOpened():
                logger.error(f"Failed to open camera {self.config.name}")
                return False
            
            # Set resolution
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
            
            # Start capture thread
            self.is_running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            
            logger.info(f"✅ Camera {self.config.name} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting camera {self.config.name}: {e}")
            return False
    
    def _capture_loop(self):
        """Capture frames in background thread"""
        while self.is_running:
            try:
                ret, frame = self.capture.read()
                
                if not ret:
                    self.error_count += 1
                    logger.warning(f"Failed to read frame from {self.config.name} (errors: {self.error_count})")
                    
                    if self.error_count >= self.max_errors:
                        logger.error(f"Too many errors for {self.config.name}, stopping...")
                        self.stop()
                        break
                    
                    # Try to reconnect
                    asyncio.sleep(1)
                    continue
                
                # Reset error count on success
                self.error_count = 0
                
                # Store latest frame
                self.last_frame = frame
                
                # Update queue (remove old frame if full)
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except:
                        pass
                
                self.frame_queue.put(frame)
                
            except Exception as e:
                logger.error(f"Error in capture loop for {self.config.name}: {e}")
                asyncio.sleep(1)
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get latest frame"""
        return self.last_frame
    
    def get_frame_from_queue(self) -> Optional[np.ndarray]:
        """Get frame from queue (blocking)"""
        try:
            return self.frame_queue.get(timeout=1)
        except:
            return None
    
    def stop(self):
        """Stop camera capture"""
        logger.info(f"Stopping camera {self.config.name}")
        self.is_running = False
        
        if self.thread:
            self.thread.join(timeout=2)
        
        if self.capture:
            self.capture.release()
        
        logger.info(f"Camera {self.config.name} stopped")
    
    def is_alive(self) -> bool:
        """Check if camera is running"""
        return self.is_running and self.thread and self.thread.is_alive()


class CameraManager:
    """Manage multiple RTSP cameras"""
    
    def __init__(self):
        self.cameras: Dict[str, RTSPCamera] = {}
        self._initialized = False
    
    def add_camera(self, config: CameraConfig) -> bool:
        """Add and start a camera"""
        if config.id in self.cameras:
            logger.warning(f"Camera {config.id} already exists")
            return False
        
        camera = RTSPCamera(config)
        if camera.start():
            self.cameras[config.id] = camera
            return True
        return False
    
    def get_camera(self, camera_id: str) -> Optional[RTSPCamera]:
        """Get camera by ID"""
        return self.cameras.get(camera_id)
    
    def get_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """Get latest frame from camera"""
        camera = self.cameras.get(camera_id)
        if camera:
            return camera.get_frame()
        return None
    
    def get_all_frames(self) -> Dict[str, np.ndarray]:
        """Get latest frames from all cameras"""
        frames = {}
        for camera_id, camera in self.cameras.items():
            frame = camera.get_frame()
            if frame is not None:
                frames[camera_id] = frame
        return frames
    
    def stop_camera(self, camera_id: str):
        """Stop specific camera"""
        camera = self.cameras.get(camera_id)
        if camera:
            camera.stop()
            del self.cameras[camera_id]
    
    def stop_all(self):
        """Stop all cameras"""
        for camera in self.cameras.values():
            camera.stop()
        self.cameras.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all cameras"""
        status = {}
        for camera_id, camera in self.cameras.items():
            status[camera_id] = {
                'name': camera.config.name,
                'ip': camera.config.ip,
                'running': camera.is_alive(),
                'errors': camera.error_count
            }
        return status


# Global camera manager instance
_camera_manager: Optional[CameraManager] = None


def get_camera_manager() -> CameraManager:
    """Get or create global camera manager"""
    global _camera_manager
    if _camera_manager is None:
        _camera_manager = CameraManager()
    return _camera_manager


async def initialize_cameras():
    """Initialize all configured cameras"""
    manager = get_camera_manager()
    
    # Camera 1: 192.168.1.11
    cam1_config = CameraConfig(
        id="cam1",
        name="Camera 1",
        rtsp_url="rtsp://admin:abcd12345@{ip}/cam/realmonitor?channel=1&subtype=1",
        username="admin",
        password="abcd12345",
        ip="192.168.1.11",
        width=640,
        height=480,
        fps=5
    )
    
    # Camera 2: 192.168.1.13 (fallback to 192.168.1.9)
    cam2_config = CameraConfig(
        id="cam2",
        name="Camera 2",
        rtsp_url="rtsp://admin:abcd12345@{ip}/cam/realmonitor?channel=1&subtype=1",
        username="admin",
        password="abcd12345",
        ip="192.168.1.13",  # Try this first
        width=640,
        height=480,
        fps=5
    )
    
    # Start cameras
    success1 = manager.add_camera(cam1_config)
    if success1:
        logger.info("✅ Camera 1 initialized")
    else:
        logger.error("❌ Failed to initialize Camera 1")
    
    success2 = manager.add_camera(cam2_config)
    if not success2:
        logger.warning("Trying fallback IP for Camera 2...")
        cam2_config.ip = "192.168.1.9"
        success2 = manager.add_camera(cam2_config)
    
    if success2:
        logger.info("✅ Camera 2 initialized")
    else:
        logger.error("❌ Failed to initialize Camera 2")
    
    return manager
