"""
Vision AI Pipeline Orchestrator
Coordinates RTSP → Detection → VLM inference
"""

import os
import time
import queue
import logging
import threading
from typing import Dict, Optional, List
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


class VisionPipeline:
    """
    Main pipeline orchestrator
    Manages: RTSP streams → Detection → VLM analysis
    """
    
    def __init__(
        self,
        camera_urls: Dict[str, str],
        vllm_api_url: str,
        detection_conf: float = 0.5,
        sample_rate: float = 1.0
    ):
        """
        Initialize pipeline
        
        Args:
            camera_urls: Dict of {camera_id: rtsp_url}
            vllm_api_url: vLLM API endpoint
            detection_conf: Detection confidence threshold
            sample_rate: Frame sampling rate (FPS)
        """
        self.camera_urls = camera_urls
        self.vllm_api_url = vllm_api_url
        self.detection_conf = detection_conf
        self.sample_rate = sample_rate
        
        # Components (lazy init)
        self.rtsp_manager = None
        self.detector = None
        self.vllm_client = None
        
        # Processing queues
        self.detection_queue = queue.Queue(maxsize=20)
        self.vlm_queue = queue.Queue(maxsize=10)
        
        # State
        self._running = False
        self._threads = []
        
        # Results cache
        self.latest_results = {}
        self.results_lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'frames_received': 0,
            'frames_detected': 0,
            'frames_analyzed': 0,
            'errors': 0
        }
        self.stats_lock = threading.Lock()
        
        logger.info("🚀 Vision Pipeline initialized")
        logger.info(f"   Cameras: {list(camera_urls.keys())}")
        logger.info(f"   vLLM API: {vllm_api_url}")
        logger.info(f"   Detection conf: {detection_conf}")
        logger.info(f"   Sample rate: {sample_rate} FPS")
    
    def initialize(self):
        """Initialize all components"""
        logger.info("🔧 Initializing components...")
        
        try:
            # Import services
            from .rtsp_client import RTSPManager
            from .detection import DetectionService
            from .vlm_client import VLMClient
            
            # Initialize RTSP Manager
            logger.info("📹 Initializing RTSP manager...")
            self.rtsp_manager = RTSPManager(max_queue_size=20)
            for camera_id, url in self.camera_urls.items():
                self.rtsp_manager.add_camera(
                    camera_id=camera_id,
                    rtsp_url=url,
                    sample_rate=self.sample_rate
                )
            
            # Initialize Detection Service
            logger.info("🔍 Initializing detection service...")
            detection_device = os.getenv('DETECTION_DEVICE', 'cpu')
            self.detector = DetectionService(
                model_name="yolov8n.pt",
                conf_threshold=self.detection_conf,
                device=detection_device,
                batch_size=2
            )
            
            # Initialize VLM Client
            logger.info("🧠 Initializing VLM client...")
            self.vllm_client = VLMClient(api_url=self.vllm_api_url)
            
            logger.info("✅ All components initialized")
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise
    
    def start(self):
        """Start pipeline"""
        if self._running:
            logger.warning("⚠️  Pipeline already running")
            return
        
        self._running = True
        
        # Start RTSP streams
        logger.info("▶️  Starting RTSP streams...")
        self.rtsp_manager.start_all()
        
        # Start worker threads
        logger.info("▶️  Starting worker threads...")
        
        # Detection worker
        t1 = threading.Thread(target=self._detection_worker, daemon=True)
        t1.start()
        self._threads.append(t1)
        
        # VLM worker
        t2 = threading.Thread(target=self._vlm_worker, daemon=True)
        t2.start()
        self._threads.append(t2)
        
        # Frame coordinator
        t3 = threading.Thread(target=self._frame_coordinator, daemon=True)
        t3.start()
        self._threads.append(t3)
        
        logger.info(f"✅ Pipeline started with {len(self._threads)} workers")
    
    def stop(self):
        """Stop pipeline"""
        logger.info("⏹️  Stopping pipeline...")
        self._running = False
        
        # Stop RTSP streams
        if self.rtsp_manager:
            self.rtsp_manager.stop_all()
        
        # Wait for threads
        for t in self._threads:
            t.join(timeout=5)
        
        logger.info("✅ Pipeline stopped")
    
    def _frame_coordinator(self):
        """Coordinate frame flow from RTSP to detection"""
        logger.info("🎬 Frame coordinator started")
        
        while self._running:
            try:
                # Get frame from RTSP
                frame_data = self.rtsp_manager.get_frame(timeout=1.0)
                
                if frame_data is None:
                    continue
                
                # Update stats
                with self.stats_lock:
                    self.stats['frames_received'] += 1
                
                # Forward to detection queue
                try:
                    self.detection_queue.put_nowait(frame_data)
                except queue.Full:
                    # Drop frame if detection is backlogged
                    pass
                
            except Exception as e:
                logger.error(f"❌ Frame coordinator error: {e}")
                with self.stats_lock:
                    self.stats['errors'] += 1
                time.sleep(0.1)
        
        logger.info("🎬 Frame coordinator stopped")
    
    def _detection_worker(self):
        """Process detection on frames"""
        logger.info("🔍 Detection worker started")
        
        batch = []
        batch_timeout = 0.5  # 500ms to collect batch
        last_batch_time = time.time()
        
        while self._running:
            try:
                # Collect frames for batch
                try:
                    frame_data = self.detection_queue.get(timeout=0.1)
                    batch.append(frame_data)
                except queue.Empty:
                    pass
                
                # Process batch if ready
                current_time = time.time()
                should_process = (
                    len(batch) >= 2 or  # Batch size reached
                    (len(batch) > 0 and current_time - last_batch_time > batch_timeout)
                )
                
                if should_process:
                    # Prepare batch
                    images = [item['frame'] for item in batch]
                    
                    # Run detection
                    detections = self.detector.detect(images, return_crops=True)
                    
                    # Package results
                    for frame_data, detection in zip(batch, detections):
                        result = {
                            **frame_data,
                            'detection': detection,
                            'detection_summary': self.detector.get_summary(detection)
                        }
                        
                        # Update latest results
                        with self.results_lock:
                            self.latest_results[frame_data['camera_id']] = result
                        
                        # Send to VLM if objects detected
                        if detection['boxes']:
                            try:
                                self.vlm_queue.put_nowait(result)
                            except queue.Full:
                                pass  # Skip VLM if busy
                    
                    # Update stats
                    with self.stats_lock:
                        self.stats['frames_detected'] += len(batch)
                    
                    # Reset batch
                    batch = []
                    last_batch_time = current_time
                
            except Exception as e:
                logger.error(f"❌ Detection worker error: {e}")
                with self.stats_lock:
                    self.stats['errors'] += 1
                batch = []
                time.sleep(0.1)
        
        logger.info("🔍 Detection worker stopped")
    
    def _vlm_worker(self):
        """Process VLM analysis"""
        logger.info("🧠 VLM worker started")
        
        while self._running:
            try:
                # Get frame with detections
                result = self.vlm_queue.get(timeout=1.0)
                
                # Prepare prompt
                detection = result['detection']
                prompt = self._create_vlm_prompt(detection)
                
                # Get main frame or first crop
                image = result['frame']
                if detection.get('crops'):
                    image = detection['crops'][0]  # Analyze first detected object
                
                # Call VLM
                try:
                    analysis = self.vllm_client.analyze(image, prompt)
                    result['vlm_analysis'] = analysis
                    
                    # Update results
                    with self.results_lock:
                        self.latest_results[result['camera_id']] = result
                    
                    # Update stats
                    with self.stats_lock:
                        self.stats['frames_analyzed'] += 1
                    
                    logger.info(
                        f"🧠 [{result['camera_id']}] VLM: {analysis[:100]}..."
                    )
                    
                except Exception as e:
                    logger.error(f"❌ VLM inference failed: {e}")
                    result['vlm_analysis'] = f"Error: {str(e)}"
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"❌ VLM worker error: {e}")
                with self.stats_lock:
                    self.stats['errors'] += 1
                time.sleep(0.1)
        
        logger.info("🧠 VLM worker stopped")
    
    def _create_vlm_prompt(self, detection: Dict) -> str:
        """Create VLM prompt from detection results"""
        if not detection['class_names']:
            return "Describe what you see in this image."
        
        classes = ", ".join(set(detection['class_names']))
        return (
            f"I detected the following objects: {classes}. "
            f"Please describe the scene and what these objects are doing."
        )
    
    def get_latest_results(self) -> Dict:
        """Get latest results for all cameras"""
        with self.results_lock:
            return dict(self.latest_results)
    
    def get_stats(self) -> Dict:
        """Get pipeline statistics"""
        with self.stats_lock:
            status = self.rtsp_manager.get_all_status() if self.rtsp_manager else {}
            return {
                **dict(self.stats),
                'running': self._running,
                'camera_status': status
            }


# Test code
if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get configuration
    camera_urls = {
        'camera1': os.getenv('CAMERA_1_URL'),
        'camera2': os.getenv('CAMERA_2_URL')
    }
    
    vllm_url = os.getenv('VLLM_API_URL', 'http://localhost:8000/v1')
    
    if not all(camera_urls.values()):
        logger.error("❌ Camera URLs not configured in .env")
        sys.exit(1)
    
    # Create and test pipeline
    logger.info("=" * 70)
    logger.info("VISION AI PIPELINE TEST")
    logger.info("=" * 70)
    
    pipeline = VisionPipeline(
        camera_urls=camera_urls,
        vllm_api_url=vllm_url,
        detection_conf=0.5,
        sample_rate=1.0
    )
    
    try:
        pipeline.initialize()
        pipeline.start()
        
        logger.info("\n⏱️  Running for 30 seconds...")
        logger.info("Press Ctrl+C to stop early\n")
        
        for i in range(30):
            time.sleep(1)
            
            if (i + 1) % 10 == 0:
                stats = pipeline.get_stats()
                logger.info(f"\n📊 Stats at {i+1}s:")
                logger.info(f"   Frames received: {stats['frames_received']}")
                logger.info(f"   Frames detected: {stats['frames_detected']}")
                logger.info(f"   Frames analyzed: {stats['frames_analyzed']}")
                logger.info(f"   Errors: {stats['errors']}")
                
                results = pipeline.get_latest_results()
                for camera_id, result in results.items():
                    logger.info(f"\n   [{camera_id}]:")
                    logger.info(f"      Detection: {result.get('detection_summary', 'N/A')}")
                    if 'vlm_analysis' in result:
                        logger.info(f"      VLM: {result['vlm_analysis'][:80]}...")
        
        logger.info("\n✅ Test complete")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pipeline.stop()
        logger.info("=" * 70)
