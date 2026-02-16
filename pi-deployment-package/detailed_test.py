#!/usr/bin/env python3
"""
Detailed inference với multi-turn conversation để lấy thông tin đầy đủ hơn
"""

import base64
import json
import sys
import requests
from typing import List, Dict

class DetailedVisionAnalyzer:
    def __init__(self, server_url="http://localhost:8080"):
        self.server_url = server_url
        self.conversation: List[Dict] = []
    
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 data URL"""
        with open(image_path, "rb") as f:
            image_data = f.read()
        b64_data = base64.b64encode(image_data).decode('utf-8')
        return f"data:image/jpeg;base64,{b64_data}"
    
    def ask(self, question: str, image_url: str = None) -> str:
        """Hỏi một câu hỏi (có thể kèm image)"""
        
        # Build message content
        content = []
        if image_url:
            content.append({"type": "image_url", "image_url": {"url": image_url}})
        content.append({"type": "text", "text": question})
        
        # Add to conversation
        self.conversation.append({
            "role": "user",
            "content": content
        })
        
        # Prepare request
        payload = {
            "messages": self.conversation,
            "max_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/v1/chat/completions",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    answer = result["choices"][0]["message"]["content"]
                    
                    # Add assistant response to conversation
                    self.conversation.append({
                        "role": "assistant",
                        "content": answer
                    })
                    
                    return answer
                else:
                    return f"Error: Invalid response - {result}"
            else:
                return f"HTTP Error {response.status_code}: {response.text}"
                
        except Exception as e:
            return f"Error: {e}"
    
    def reset(self):
        """Reset conversation"""
        self.conversation = []


def analyze_image_detailed(image_path: str):
    """Phân tích ảnh với nhiều câu hỏi chi tiết"""
    
    print(f"\n{'='*70}")
    print(f"🔍 PHÂN TÍCH CHI TIẾT: {image_path}")
    print(f"{'='*70}\n")
    
    analyzer = DetailedVisionAnalyzer()
    image_url = analyzer.encode_image(image_path)
    
    # Danh sách câu hỏi chi tiết
    questions = [
        "Mô tả tổng quan bức ảnh này?",
        "Có những vật thể gì trong ảnh?",
        "Màu sắc của các vật thể như thế nào?",
        "Có bao nhiêu vật thể? Đếm cụ thể.",
        "Bố cục và vị trí các vật thể ra sao?",
        "Nền của ảnh là gì? Màu gì?",
        "Có chi tiết đặc biệt nào đáng chú ý không?"
    ]
    
    results = []
    
    for i, question in enumerate(questions, 1):
        print(f"❓ Câu {i}: {question}")
        
        # Câu hỏi đầu tiên kèm ảnh, các câu sau chỉ text
        if i == 1:
            answer = analyzer.ask(question, image_url)
        else:
            answer = analyzer.ask(question)
        
        print(f"💬 {answer}\n")
        results.append({
            "question": question,
            "answer": answer
        })
    
    # Tổng hợp
    print(f"\n{'='*70}")
    print("📋 TỔNG HỢP PHÂN TÍCH:")
    print(f"{'='*70}\n")
    
    # Combine all answers into a coherent description
    full_description = " ".join([item['answer'] for item in results])
    
    # Clean up duplicates and format better
    sentences = full_description.split('.')
    unique_sentences = []
    seen = set()
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and sentence not in seen and len(sentence) > 10:
            unique_sentences.append(sentence)
            seen.add(sentence)
    
    formatted_description = ". ".join(unique_sentences) + "."
    
    print("🖼️ MÔ TẢ TỔNG HỢP:\n")
    print(formatted_description)
    
    print(f"\n\n📊 CHI TIẾT TỪNG CÂU HỎI:\n")
    for i, item in enumerate(results, 1):
        print(f"{i}. {item['question']}")
        print(f"   → {item['answer']}\n")
    
    print(f"{'='*70}\n")
    
    return results, formatted_description


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python detailed_test.py <image_path>")
        sys.exit(1)
    
    analyze_image_detailed(sys.argv[1])
