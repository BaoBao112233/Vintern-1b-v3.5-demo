#!/usr/bin/env python3
"""
Quick test - Analyze với PC VLLM service
"""

import requests
import json
import sys

API_URL = "http://localhost:8005"

print("=" * 70)
print("🧪 TEST ANALYZE WITH PC VLLM SERVICE")
print("=" * 70)
print()

# Test 1: Capture frame
print("📸 Step 1: Capture frame từ Camera 1...")
response = requests.get(f"{API_URL}/api/capture/1", timeout=10)

if response.status_code == 200:
    print(f"✅ Captured: {len(response.content)} bytes")
    with open("/tmp/test_frame.jpg", "wb") as f:
        f.write(response.content)
else:
    print(f"❌ Failed: {response.status_code}")
    sys.exit(1)

print()

# Test 2: Analyze với PC VLLM
print("🤖 Step 2: Analyze với PC VLLM (192.168.1.3:8080)...")
print("   Prompt: 'Describe what you see in this image'")
print()

payload = {
    "camera_id": 1,
    "prompt": "Describe what you see in this image. Are there any people or vehicles?",
    "save_frame": True
}

print("⏳ Sending request... (có thể mất 5-10 giây)")
response = requests.post(
    f"{API_URL}/api/analyze",
    json=payload,
    timeout=60
)

print()

if response.status_code == 200:
    result = response.json()
    
    print("=" * 70)
    print("📊 RESULT")
    print("=" * 70)
    print(f"Success: {result['success']}")
    print(f"Latency: {result['latency_ms']:.1f}ms")
    print()
    
    if result['success']:
        print("🤖 AI Response:")
        print("-" * 70)
        print(result['response'])
        print("-" * 70)
        print()
        print(f"✅ Frame saved: {result.get('frame_saved', 'N/A')}")
    else:
        print(f"❌ Error: {result['error']}")
        
else:
    print(f"❌ HTTP {response.status_code}")
    print(response.text)

print()
print("=" * 70)
