#!/usr/bin/env python3
"""
Quick test inference với image
"""

import base64
import json
import sys
import requests

def test_inference(image_path: str):
    """Test inference với image"""
    
    print(f"🖼️ Testing with image: {image_path}")
    
    # 1. Encode image
    print("📦 Encoding image...")
    with open(image_path, "rb") as f:
        image_data = f.read()
    b64_data = base64.b64encode(image_data).decode('utf-8')
    data_url = f"data:image/jpeg;base64,{b64_data}"
    
    # 2. Prepare request  
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": "Mô tả chi tiết ảnh này. Có những loại trái cây gì? Màu sắc như thế nào? Bố cục ra sao? Có bao nhiêu quả? Nền là gì?"}
                ]
            }
        ],
        "max_tokens": 1024,
        "temperature": 0.9,
        "top_p": 0.95,
        "repeat_penalty": 1.15,
        "min_p": 0.05,
        "stop": [],
        "stream": False
    }
    
    # 3. Send request
    print("🚀 Sending request to server...")
    try:
        response = requests.post(
            "http://localhost:8080/v1/chat/completions",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                
                print("\n✅ SUCCESS!")
                print("="*60)
                print(content)
                print("="*60)
                
                if "usage" in result:
                    usage = result["usage"]
                    print(f"\n📊 Tokens: {usage.get('total_tokens', 'N/A')}")
                
                return True
            else:
                print(f"\n❌ Invalid response: {result}")
                return False
        else:
            print(f"\n❌ HTTP Error {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quick_test.py <image_path>")
        sys.exit(1)
    
    test_inference(sys.argv[1])
