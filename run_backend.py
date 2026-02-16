#!/usr/bin/env python3
"""
Simplified backend runner for testing
Runs without vLLM (detection + RTSP only)
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_rtsp_detection():
    """Test RTSP + Detection pipeline (without VLM)"""
    
    logger.info("=" * 70)
    logger.info("TESTING RTSP + DETECTION PIPELINE")
    logger.info("=" * 70)
    
    from app.services.rtsp_client import RTSPManager
    from app.services.detection import DetectionService
    
    # Get config
    camera1_url = os.getenv('CAMERA_1_URL')
    camera2_url = os.getenv('CAMERA_2_URL')
    detection_device = os.getenv('DETECTION_DEVICE', 'cpu')
    
    if not camera1_url or not camera2_url:
        logger.error("❌ Camera URLs not configured")
        return 1
    
    try:
        # Initialize RTSP manager
        logger.info("\n📹 Initializing RTSP manager...")
        rtsp_manager = RTSPManager(max_queue_size=10)
        rtsp_manager.add_camera('camera1', camera1_url, 1.0)
        rtsp_manager.add_camera('camera2', camera2_url, 1.0)
        
        # Initialize detector
        logger.info(f"\n🔍 Initializing detector (device: {detection_device})...")
        detector = DetectionService(
            model_name='yolov8n.pt',
            conf_threshold=0.5,
            device=detection_device,
            batch_size=2
        )
        
        # Start RTSP streams
        logger.info("\n▶️  Starting RTSP streams...")
        rtsp_manager.start_all()
        
        # Process frames
        logger.info("\n🎬 Processing frames for 30 seconds...")
        logger.info("Press Ctrl+C to stop early\n")
        
        start_time = time.time()
        frame_count = 0
        batch = []
        
        while time.time() - start_time < 30:
            # Get frame
            frame_data = rtsp_manager.get_frame(timeout=1.0)
            
            if frame_data is None:
                continue
            
            batch.append(frame_data)
            
            # Process batch when ready
            if len(batch) >= 2:
                images = [item['frame'] for item in batch]
                
                # Run detection
                detections = detector.detect(images)
                
                # Log results
                for frame_item, detection in zip(batch, detections):
                    camera_id = frame_item['camera_id']
                    summary = detector.get_summary(detection)
                    frame_num = frame_item['frame_number']
                    
                    logger.info(f"  [{camera_id}] Frame {frame_num}: {summary}")
                    frame_count += len(batch)
                
                batch = []
                time.sleep(0.5)  # Brief pause
        
        # Stats
        logger.info("\n📊 Final Statistics:")
        elapsed = time.time() - start_time
        logger.info(f"   Duration: {elapsed:.1f}s")
        logger.info(f"   Frames processed: {frame_count}")
        logger.info(f"   FPS: {frame_count/elapsed:.2f}")
        
        status = rtsp_manager.get_all_status()
        logger.info(f"\n📡 Camera Status:")
        for cam_id, stat in status.items():
            logger.info(f"   {cam_id}: {stat}")
        
        # Cleanup
        rtsp_manager.stop_all()
        
        logger.info("\n✅ Test complete")
        logger.info("=" * 70)
        return 0
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_backend():
    """Run full backend with FastAPI"""
    
    logger.info("=" * 70)
    logger.info("STARTING VINTERN VISION AI BACKEND")
    logger.info("=" * 70)
    
    import uvicorn
    from app.main_new import app
    
    host = os.getenv('BACKEND_HOST', '0.0.0.0')
    port = int(os.getenv('BACKEND_PORT', '8001'))
    
    logger.info(f"\n🚀 Server starting on http://{host}:{port}")
    logger.info("📡 WebSocket available at ws://{host}:{port}/ws")
    logger.info("\n⚠️  Note: vLLM must be running separately")
    logger.info("   Start with: docker compose -f docker-compose.vllm.yml up vllm")
    logger.info("=" * 70)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Vintern Vision AI Backend Runner")
    parser.add_argument(
        '--mode',
        choices=['test', 'run'],
        default='test',
        help='Mode: test (RTSP+Detection only) or run (full backend)'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'test':
        sys.exit(test_rtsp_detection())
    else:
        run_backend()
