"""
RTSP Client Service
Handles streaming from multiple RTSP cameras with auto-reconnect
"""

import cv2
import threading
import queue
import time
import logging
from typing import Optional, Callable, Dict
import numpy as np

logger = logging.getLogger(__name__)


class RTSPClient:
    """RTSP Camera Client with auto-reconnect"""
    
    def __init__(
        self,
        camera_id: str,
        rtsp_url: str,
        frame_queue: queue.Queue,
        sample_rate: float = 1.0,
        timeout: int = 10,
        max_reconnect_attempts: int = 5
    ):
        """
        Initialize RTSP client
        
        Args:
            camera_id: Unique camera identifier
            rtsp_url: RTSP stream URL
            frame_queue: Queue to put frames
            sample_rate: Frames per second to sample
            timeout: Connection timeout in seconds
            max_reconnect_attempts: Max reconnection attempts
        """
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.frame_queue = frame_queue
        self.sample_rate = sample_rate
        self.timeout = timeout
        self.max_reconnect_attempts = max_reconnect_attempts
        
        self._cap: Optional[cv2.VideoCapture] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._connected = False
        self._last_frame_time = 0
        self._frame_count = 0
        self._error_count = 0
        
        logger.info(f"📹 [{camera_id}] Initialized")
        logger.info(f"   URL: {rtsp_url[:30]}...{rtsp_url[-20:]}")
        logger.info(f"   Sample rate: {sample_rate} FPS")
    
    def connect(self) -> bool:
        """
        Connect to RTSP stream
        
        Returns:
            True if connected successfully
        """
        try:
            logger.info(f"📡 [{self.camera_id}] Connecting...")
            
            self._cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            self._cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, self.timeout * 1000)
            self._cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, self.timeout * 1000)
            
            if not self._cap.isOpened():
                logger.error(f"❌ [{self.camera_id}] Failed to open stream")
                return False
            
            # Test read
            ret, frame = self._cap.read()
            if not ret or frame is None:
                logger.error(f"❌ [{self.camera_id}] Failed to read frame")
                self._cap.release()
                return False
            
            self._connected = True
            width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self._cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"✅ [{self.camera_id}] Connected: {width}x{height} @ {fps} FPS")
            return True
            
        except Exception as e:
            logger.error(f"❌ [{self.camera_id}] Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from stream"""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._connected = False
        logger.info(f"🔌 [{self.camera_id}] Disconnected")
    
    def start(self):
        """Start streaming thread"""
        if self._running:
            logger.warning(f"⚠️  [{self.camera_id}] Already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._thread.start()
        logger.info(f"▶️  [{self.camera_id}] Started")
    
    def stop(self):
        """Stop streaming thread"""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5)
        self.disconnect()
        logger.info(f"⏹️  [{self.camera_id}] Stopped")
    
    def _stream_loop(self):
        """Main streaming loop with auto-reconnect"""
        reconnect_attempts = 0
        frame_interval = 1.0 / self.sample_rate if self.sample_rate > 0 else 0
        
        while self._running:
            # Connect if not connected
            if not self._connected:
                if reconnect_attempts >= self.max_reconnect_attempts:
                    logger.error(
                        f"❌ [{self.camera_id}] Max reconnect attempts reached"
                    )
                    time.sleep(5)
                    reconnect_attempts = 0
                    continue
                
                success = self.connect()
                if not success:
                    reconnect_attempts += 1
                    wait_time = min(2 ** reconnect_attempts, 30)
                    logger.warning(
                        f"🔄 [{self.camera_id}] Retry in {wait_time}s "
                        f"(attempt {reconnect_attempts}/{self.max_reconnect_attempts})"
                    )
                    time.sleep(wait_time)
                    continue
                
                reconnect_attempts = 0
            
            # Read frame
            try:
                ret, frame = self._cap.read()
                
                if not ret or frame is None:
                    logger.warning(f"⚠️  [{self.camera_id}] Frame read failed")
                    self._error_count += 1
                    
                    if self._error_count > 10:
                        logger.error(f"❌ [{self.camera_id}] Too many errors, reconnecting")
                        self.disconnect()
                        self._error_count = 0
                    
                    time.sleep(0.1)
                    continue
                
                # Reset error count on success
                self._error_count = 0
                
                # Sample rate control
                current_time = time.time()
                if frame_interval > 0:
                    elapsed = current_time - self._last_frame_time
                    if elapsed < frame_interval:
                        time.sleep(frame_interval - elapsed)
                        continue
                
                self._last_frame_time = current_time
                self._frame_count += 1
                
                # Put frame in queue (non-blocking)
                try:
                    self.frame_queue.put_nowait({
                        'camera_id': self.camera_id,
                        'frame': frame,
                        'timestamp': current_time,
                        'frame_number': self._frame_count
                    })
                except queue.Full:
                    # Drop frame if queue is full
                    pass
                
            except Exception as e:
                logger.error(f"❌ [{self.camera_id}] Stream error: {e}")
                self.disconnect()
                time.sleep(1)
    
    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self._connected
    
    @property
    def frame_count(self) -> int:
        """Get total frames captured"""
        return self._frame_count
    
    def get_status(self) -> Dict:
        """Get client status"""
        return {
            'camera_id': self.camera_id,
            'connected': self._connected,
            'running': self._running,
            'frame_count': self._frame_count,
            'error_count': self._error_count
        }


class RTSPManager:
    """Manages multiple RTSP clients"""
    
    def __init__(self, max_queue_size: int = 10):
        """
        Initialize RTSP manager
        
        Args:
            max_queue_size: Maximum frame queue size
        """
        self.clients: Dict[str, RTSPClient] = {}
        self.frame_queue = queue.Queue(maxsize=max_queue_size)
        logger.info(f"🎥 RTSP Manager initialized (queue size: {max_queue_size})")
    
    def add_camera(
        self,
        camera_id: str,
        rtsp_url: str,
        sample_rate: float = 1.0
    ):
        """
        Add camera to manager
        
        Args:
            camera_id: Unique camera ID
            rtsp_url: RTSP stream URL
            sample_rate: Sampling rate (FPS)
        """
        if camera_id in self.clients:
            logger.warning(f"⚠️  Camera {camera_id} already exists")
            return
        
        client = RTSPClient(
            camera_id=camera_id,
            rtsp_url=rtsp_url,
            frame_queue=self.frame_queue,
            sample_rate=sample_rate
        )
        
        self.clients[camera_id] = client
        logger.info(f"✅ Camera {camera_id} added")
    
    def start_all(self):
        """Start all cameras"""
        logger.info("▶️  Starting all cameras...")
        for camera_id, client in self.clients.items():
            client.start()
        logger.info(f"✅ Started {len(self.clients)} camera(s)")
    
    def stop_all(self):
        """Stop all cameras"""
        logger.info("⏹️  Stopping all cameras...")
        for camera_id, client in self.clients.items():
            client.stop()
        logger.info("✅ All cameras stopped")
    
    def get_frame(self, timeout: Optional[float] = 1.0) -> Optional[Dict]:
        """
        Get next frame from queue
        
        Args:
            timeout: Timeout in seconds
        
        Returns:
            Frame dict or None
        """
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_all_status(self) -> Dict:
        """Get status of all cameras"""
        return {
            camera_id: client.get_status()
            for camera_id, client in self.clients.items()
        }


# Test code
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    logging.basicConfig(level=logging.INFO)
    
    # Get camera URLs from environment
    camera1_url = os.getenv("CAMERA_1_URL")
    camera2_url = os.getenv("CAMERA_2_URL")
    
    if not camera1_url or not camera2_url:
        logger.error("❌ Camera URLs not found in .env")
        exit(1)
    
    # Test RTSP Manager
    logger.info("=" * 60)
    logger.info("Testing RTSP Manager")
    logger.info("=" * 60)
    
    manager = RTSPManager(max_queue_size=10)
    manager.add_camera("camera1", camera1_url, sample_rate=1.0)
    manager.add_camera("camera2", camera2_url, sample_rate=1.0)
    
    manager.start_all()
    
    try:
        logger.info("\n📸 Capturing frames for 10 seconds...")
        start_time = time.time()
        frame_counts = {}
        
        while time.time() - start_time < 10:
            frame_data = manager.get_frame(timeout=1.0)
            if frame_data:
                camera_id = frame_data['camera_id']
                frame_counts[camera_id] = frame_counts.get(camera_id, 0) + 1
                
                if frame_counts[camera_id] % 5 == 0:
                    logger.info(
                        f"  [{camera_id}] Frame {frame_counts[camera_id]}: "
                        f"{frame_data['frame'].shape}"
                    )
        
        logger.info("\n📊 Final Statistics:")
        for camera_id, count in frame_counts.items():
            logger.info(f"  {camera_id}: {count} frames")
        
        logger.info("\n📡 Camera Status:")
        for camera_id, status in manager.get_all_status().items():
            logger.info(f"  {camera_id}: {status}")
        
        logger.info("\n✅ Test complete")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    finally:
        manager.stop_all()
        logger.info("=" * 60)
