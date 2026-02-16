#!/usr/bin/env python3
"""
RTSP Camera Connection Test
Tests connectivity to both Dahua cameras with TCP transport
"""

import cv2
import sys
import time
from pathlib import Path

# Camera URLs
CAMERAS = {
    "Camera 1": "rtsp://admin:abcd12345@192.168.1.4/cam/realmonitor?channel=1&subtype=1",
    "Camera 2": "rtsp://admin:abcd12345@192.168.1.7/cam/realmonitor?channel=1&subtype=1"
}

def test_camera(name: str, url: str, duration: int = 5) -> bool:
    """
    Test RTSP camera connection and frame capture
    
    Args:
        name: Camera name for logging
        url: RTSP URL
        duration: Test duration in seconds
    
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Testing {name}")
    print(f"URL: {url[:30]}...{url[-20:]}")  # Mask password
    print(f"{'='*60}")
    
    # Configure OpenCV for RTSP
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    
    # Set TCP transport (critical for Dahua cameras)
    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)
    
    if not cap.isOpened():
        print(f"❌ FAIL: Cannot open {name}")
        return False
    
    print(f"✅ Connection established")
    
    # Get camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"   Resolution: {width}x{height}")
    print(f"   FPS: {fps}")
    
    # Test frame capture
    frame_count = 0
    start_time = time.time()
    success_count = 0
    
    print(f"\n📸 Capturing frames for {duration} seconds...")
    
    while time.time() - start_time < duration:
        ret, frame = cap.read()
        frame_count += 1
        
        if ret:
            success_count += 1
            if frame_count % 10 == 0:
                print(f"   Frame {frame_count}: OK (shape: {frame.shape})")
        else:
            print(f"   Frame {frame_count}: FAIL")
        
        time.sleep(0.1)  # 10 FPS test rate
    
    cap.release()
    
    # Calculate statistics
    elapsed = time.time() - start_time
    actual_fps = success_count / elapsed
    success_rate = (success_count / frame_count * 100) if frame_count > 0 else 0
    
    print(f"\n📊 Results:")
    print(f"   Total frames attempted: {frame_count}")
    print(f"   Successful frames: {success_count}")
    print(f"   Success rate: {success_rate:.1f}%")
    print(f"   Actual FPS: {actual_fps:.2f}")
    
    if success_rate >= 90:
        print(f"✅ {name} PASSED")
        return True
    else:
        print(f"❌ {name} FAILED (low success rate)")
        return False

def main():
    """Main test runner"""
    print("🎥 RTSP Camera Connection Test")
    print("=" * 60)
    print("Testing 2 Dahua cameras with TCP transport")
    print("This will take ~10 seconds per camera")
    print("=" * 60)
    
    results = {}
    
    for name, url in CAMERAS.items():
        try:
            results[name] = test_camera(name, url, duration=5)
        except Exception as e:
            print(f"\n❌ Exception during {name} test:")
            print(f"   {type(e).__name__}: {e}")
            results[name] = False
        
        time.sleep(1)  # Brief pause between tests
    
    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"{'='*60}")
    
    if all_passed:
        print("🎉 All cameras working!")
        print("\n✅ System ready for frame extraction pipeline")
        return 0
    else:
        print("⚠️  Some cameras failed")
        print("\n🔧 Troubleshooting:")
        print("   1. Check camera IP addresses")
        print("   2. Verify credentials (admin:abcd12345)")
        print("   3. Check network connectivity")
        print("   4. Ensure cameras are powered on")
        print("   5. Try: ffmpeg -rtsp_transport tcp -i CAMERA_URL -t 5 test.mp4")
        return 1

if __name__ == "__main__":
    sys.exit(main())
