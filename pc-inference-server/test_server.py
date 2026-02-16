#!/usr/bin/env python3
"""
Test PC Inference Server
Test OpenAI-compatible API endpoint
"""

import base64
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path


def encode_image_to_base64(image_path: str) -> str:
    """Encode image to base64 URL format"""
    with open(image_path, "rb") as f:
        image_data = f.read()
    b64_data = base64.b64encode(image_data).decode('utf-8')
    
    # Detect image format
    if image_path.lower().endswith('.png'):
        mime_type = 'image/png'
    elif image_path.lower().endswith(('.jpg', '.jpeg')):
        mime_type = 'image/jpeg'
    else:
        mime_type = 'image/jpeg'  # default
    
    return f"data:{mime_type};base64,{b64_data}"


def test_health(server_url: str = "http://localhost:8080"):
    """Test server health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    try:
        with urllib.request.urlopen(f"{server_url}/health") as response:
            data = json.loads(response.read().decode())
            print(f"✅ Health Check: {data}")
            return True
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False


def test_inference(
    server_url: str = "http://localhost:8080",
    image_path: str = None,
    prompt: str = "Mô tả những gì bạn thấy trong ảnh này."
):
    """Test inference with image"""
    print("\n=== Testing Inference ===")
    
    if not image_path:
        print("⚠️ No image provided, skipping inference test")
        return False
    
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return False
    
    print(f"Image: {image_path}")
    print(f"Prompt: {prompt}")
    print("Encoding image...")
    
    try:
        image_base64_url = encode_image_to_base64(image_path)
        
        # Prepare request
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_base64_url}},
                        {"type": "text", "text": prompt}
                    ]
                }
            ],
            "max_tokens": 200,
            "temperature": 0.1,
            "stream": False
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{server_url}/v1/chat/completions",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        print("Sending request to server...")
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode())
            
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print("\n✅ Inference Success!")
                print(f"\nResponse:\n{content}\n")
                
                # Show usage stats
                if "usage" in result:
                    usage = result["usage"]
                    print(f"Tokens - Prompt: {usage.get('prompt_tokens', 'N/A')}, "
                          f"Completion: {usage.get('completion_tokens', 'N/A')}, "
                          f"Total: {usage.get('total_tokens', 'N/A')}")
                
                return True
            else:
                print(f"❌ Unexpected response format: {result}")
                return False
                
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        print(f"Response: {e.read().decode()}")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


def main():
    """Main test function"""
    print("=" * 60)
    print("  PC Inference Server Test")
    print("=" * 60)
    
    server_url = "http://localhost:8080"
    
    # Test 1: Health check
    if not test_health(server_url):
        print("\n❌ Server is not running or not healthy")
        print("Please start server first: ./start_server.sh")
        sys.exit(1)
    
    # Test 2: Inference (with sample image if provided)
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        prompt = sys.argv[2] if len(sys.argv) > 2 else "Mô tả những gì bạn thấy trong ảnh này."
        test_inference(server_url, image_path, prompt)
    else:
        print("\n⚠️ No image provided for inference test")
        print("Usage: python test_server.py <image_path> [prompt]")
        print("Example: python test_server.py test.jpg 'What do you see in this image?'")
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
