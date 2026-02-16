#!/usr/bin/env python3
"""
Camera Analyzer - Standalone script
Combines RTSP capture + Vintern VLM analysis
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add backend path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.rtsp_camera import RTSPCamera
from app.services.vintern_client import VinternClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Camera Analyzer with Vintern VLM")
    parser.add_argument("--camera", type=int, choices=[1, 2], default=1, help="Camera number")
    parser.add_argument("--interval", type=int, default=5, help="Seconds between captures")
    parser.add_argument("--max-iterations", type=int, default=None, help="Max iterations")
    parser.add_argument("--save-frames", action="store_true", help="Save frames to disk")
    parser.add_argument("--backend", choices=["hf", "vllm", "pc"], default="hf", help="VLM backend")
    
    args = parser.parse_args()
    
    # Load config
    load_dotenv()
    
    # Camera setup
    camera_user = os.getenv("CAMERA_USERNAME", "admin")
    camera_pass = os.getenv("CAMERA_PASSWORD", "abcd12345")
    camera_ip = os.getenv(f"CAMERA{args.camera}_IP", f"192.168.1.{4 if args.camera == 1 else 7}")
    
    rtsp_url = f"rtsp://{camera_user}:{camera_pass}@{camera_ip}/cam/realmonitor?channel=1&subtype=1"
    camera_name = f"Camera_{args.camera}"
    
    # VLM setup
    hf_token = os.getenv("HUGGINGFACE_TOKEN", "")
    vllm_url = os.getenv("VLLM_SERVICE_URL", "http://192.168.1.16:8003")
    
    print("=" * 70)
    print("🎥 CAMERA ANALYZER WITH VINTERN VLM")
    print("=" * 70)
    print(f"Camera: {camera_name} ({camera_ip})")
    print(f"Backend: {args.backend.upper()}")
    print(f"Interval: {args.interval}s")
    print(f"Max iterations: {args.max_iterations or 'Infinite'}")
    print("=" * 70)
    print()
    
    # Initialize services
    camera = RTSPCamera(rtsp_url, camera_name)
    vlm = VinternClient(
        hf_token=hf_token,
        vllm_url=vllm_url,
        backend=args.backend
    )
    
    # Output directory
    if args.save_frames:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
    
    # Main loop
    iteration = 0
    try:
        while True:
            if args.max_iterations and iteration >= args.max_iterations:
                logger.info(f"Reached max iterations ({args.max_iterations})")
                break
            
            iteration += 1
            print(f"\n{'=' * 70}")
            print(f"📹 {camera_name} - Iteration {iteration}")
            print(f"{'=' * 70}\n")
            
            # Capture frame
            result = camera.capture_frame()
            if not result:
                logger.warning("Failed to capture frame, retrying in 5s...")
                time.sleep(5)
                continue
            
            _, frame_bytes = result
            logger.info(f"✅ Frame captured: {len(frame_bytes)} bytes")
            
            # Save if needed
            if args.save_frames:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                frame_path = output_dir / f"{camera_name}_{timestamp}.jpg"
                with open(frame_path, 'wb') as f:
                    f.write(frame_bytes)
                logger.info(f"💾 Saved: {frame_path}")
            
            # Analyze with VLM
            prompt = "Mô tả chi tiết những gì bạn thấy trong ảnh này. Có người không? Có xe không? Có vật thể đáng chú ý không?"
            
            vlm_result = vlm.analyze_image(frame_bytes, prompt)
            
            if vlm_result['success']:
                print(f"\n🤖 PHÂN TÍCH:")
                print(f"{vlm_result['response']}")
                print(f"\n⏱️  Latency: {vlm_result['latency_ms']:.1f}ms")
            else:
                print(f"\n❌ Lỗi: {vlm_result.get('error', 'Unknown error')}")
            
            # Wait
            if args.max_iterations is None or iteration < args.max_iterations:
                logger.info(f"\n⏳ Waiting {args.interval}s...")
                time.sleep(args.interval)
                
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped by user (Ctrl+C)")
    finally:
        camera.release()
        print("\n✅ Cleanup complete\n")


if __name__ == "__main__":
    main()
