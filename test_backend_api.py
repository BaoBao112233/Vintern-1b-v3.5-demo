#!/usr/bin/env python3
"""
Test Client for Vintern Camera Analysis API
Simple script to test the backend service
"""

import requests
import json
import sys
from datetime import datetime


def test_health(base_url):
    """Test health endpoint"""
    print("\n" + "=" * 70)
    print("🏥 TESTING HEALTH ENDPOINT")
    print("=" * 70)
    
    response = requests.get(f"{base_url}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_cameras(base_url):
    """Test cameras list endpoint"""
    print("\n" + "=" * 70)
    print("📹 TESTING CAMERAS ENDPOINT")
    print("=" * 70)
    
    response = requests.get(f"{base_url}/api/cameras")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_capture(base_url, camera_id=1):
    """Test capture endpoint"""
    print("\n" + "=" * 70)
    print(f"📸 TESTING CAPTURE FROM CAMERA {camera_id}")
    print("=" * 70)
    
    response = requests.get(f"{base_url}/api/capture/{camera_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        filename = f"/tmp/camera_{camera_id}_test.jpg"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"✅ Frame saved: {filename} ({len(response.content)} bytes)")
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False


def test_analyze(base_url, camera_id=1, save_frame=True):
    """Test analyze endpoint"""
    print("\n" + "=" * 70)
    print(f"🤖 TESTING ANALYSIS OF CAMERA {camera_id}")
    print("=" * 70)
    
    payload = {
        "camera_id": camera_id,
        "prompt": "Describe what you see in this image. Are there any people, vehicles, or notable objects?",
        "save_frame": save_frame
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    print("\nSending request... (this may take a moment)")
    
    response = requests.post(
        f"{base_url}/api/analyze",
        json=payload,
        timeout=60
    )
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n{'=' * 70}")
        print("📊 ANALYSIS RESULT")
        print(f"{'=' * 70}")
        print(f"Success: {result['success']}")
        print(f"Camera: {result['camera_id']}")
        print(f"Latency: {result['latency_ms']:.1f}ms")
        print(f"Timestamp: {result['timestamp']}")
        
        if result['frame_saved']:
            print(f"Frame saved: {result['frame_saved']}")
        
        if result['success']:
            print(f"\n🤖 Response:")
            print(f"{result['response']}\n")
        else:
            print(f"\n❌ Error: {result['error']}\n")
        
        return result['success']
    else:
        print(f"❌ Failed: {response.text}")
        return False


def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Vintern Camera Analysis API")
    parser.add_argument("--url", default="http://localhost:8005", help="Base URL of the API")
    parser.add_argument("--camera", type=int, default=1, choices=[1, 2], help="Camera to test")
    parser.add_argument("--test", default="all", choices=["all", "health", "cameras", "capture", "analyze"], help="Which test to run")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🧪 VINTERN CAMERA ANALYSIS API TEST CLIENT")
    print("=" * 70)
    print(f"API URL: {args.url}")
    print(f"Camera: {args.camera}")
    print(f"Test: {args.test}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    results = {}
    
    try:
        if args.test in ["all", "health"]:
            results['health'] = test_health(args.url)
        
        if args.test in ["all", "cameras"]:
            results['cameras'] = test_cameras(args.url)
        
        if args.test in ["all", "capture"]:
            results['capture'] = test_capture(args.url, args.camera)
        
        if args.test in ["all", "analyze"]:
            results['analyze'] = test_analyze(args.url, args.camera)
        
        # Summary
        print("\n" + "=" * 70)
        print("📋 TEST SUMMARY")
        print("=" * 70)
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name.capitalize()}: {status}")
        print("=" * 70)
        
        # Exit code
        if all(results.values()):
            print("\n✅ All tests passed!\n")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed\n")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Tests interrupted by user\n")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Error during testing: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
