#!/usr/bin/env python3
"""
Smart analyzer - tự động hỏi follow-up questions để lấy mô tả đầy đủ
Workaround cho limitation của Vintern-1B (model nhỏ chỉ trả lời ngắn)
"""

import base64
import json
import sys
import requests
import re

def encode_image(image_path: str) -> str:
    """Encode image to base64"""
    with open(image_path, "rb") as f:
        image_data = f.read()
    b64_data = base64.b64encode(image_data).decode('utf-8')
    return f"data:image/jpeg;base64,{b64_data}"

def ask_question(image_url: str, question: str, context: list = None) -> tuple:
    """Hỏi một câu hỏi và return (answer, tokens)"""
    
    messages = context if context else []
    
    # First message includes image
    if not context:
        messages.append({
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": question}
            ]
        })
    else:
        messages.append({
            "role": "user",
            "content": question
        })
    
    payload = {
        "messages": messages,
        "max_tokens": 512,
        "temperature": 0.7,
        "top_p": 0.9,
        "repeat_penalty": 1.15
    }
    
    try:
        response = requests.post(
            "http://localhost:8080/v1/chat/completions",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            tokens = result.get("usage", {}).get("total_tokens", 0)
            
            # Add response to context
            messages.append({
                "role": "assistant",
                "content": answer
            })
            
            return answer, tokens, messages
        else:
            return f"Error: {response.status_code}", 0, messages
            
    except Exception as e:
        return f"Error: {e}", 0, messages

def smart_analyze(image_path: str):
    """
    Phân tích thông minh:
    - Hỏi câu overview trước
    - Parse answer để tìm keywords
    - Tự động hỏi follow-up cho từng aspect
    """
    
    print(f"\n{'='*75}")
    print(f"🧠 PHÂN TÍCH THÔNG MINH: {image_path}")
    print(f"{'='*75}\n")
    
    image_url = encode_image(image_path)
    context = None
    all_info = {}
    
    # Phase 1: Overview
    print("📌 BƯỚC 1: Tổng quan chung\n")
    
    overview_q = "Bạn thấy gì trong ảnh này? Mô tả ngắn gọn."
    print(f"❓ {overview_q}")
    answer, tokens, context = ask_question(image_url, overview_q, context)
    print(f"💭 {answer}\n")
    all_info['overview'] = answer
    
    # Phase 2: Objects detail
    print("📌 BƯỚC 2: Chi tiết về vật thể\n")
    
    object_questions = [
        "Có những loại vật thể gì? Liệt kê cụ thể.",
        "Có bao nhiêu vật thể? Đếm từng loại.",
        "Vật thể nào lớn nhất? Vật thể nào nhỏ nhất?"
    ]
    
    objects_info = []
    for q in object_questions:
        print(f"❓ {q}")
        answer, _, context = ask_question(image_url, q, context)
        print(f"💭 {answer}\n")
        objects_info.append(answer)
    
    all_info['objects'] = " ".join(objects_info)
    
    # Phase 3: Colors
    print("📌 B ƯỚC 3: Màu sắc\n")
    
    color_q = "Màu sắc của từng vật thể như thế nào? Mô tả chi tiết."
    print(f"❓ {color_q}")
    answer, _, context = ask_question(image_url, color_q, context)
    print(f"💭 {answer}\n")
    all_info['colors'] = answer
    
    # Phase 4: Layout
    print("📌 BƯỚC 4: Bố cục và vị trí\n")
    
    layout_questions = [
        "Vật thể được sắp xếp như thế nào?",
        "Vị trí tương đối của các vật thể ra sao?"
    ]
    
    layout_info = []
    for q in layout_questions:
        print(f"❓ {q}")
        answer, _, context = ask_question(image_url, q, context)
        print(f"💭 {answer}\n")
        layout_info.append(answer)
    
    all_info['layout'] = " ".join(layout_info)
    
    # Phase 5: Background
    print("📌 BƯỚC 5: Nền và môi trường\n")
    
    bg_questions = [
        "Nền của ảnh là gì? Màu gì?",
        "Có yếu tố nào khác đáng chú ý không?"
    ]
    
    bg_info = []
    for q in bg_questions:
        print(f"❓ {q}")
        answer, _, context = ask_question(image_url, q, context)
        print(f"💭 {answer}\n")
        bg_info.append(answer)
    
    all_info['background'] = " ".join(bg_info)
    
    # Generate final comprehensive description
    print(f"\n{'='*75}")
    print("📝 MÔ TẢ TỔNG HỢP HOÀN CHỈNH")
    print(f"{'='*75}\n")
    
    comprehensive = f"""
{all_info['overview']} {all_info['objects']} {all_info['colors']} 
{all_info['layout']} {all_info['background']}
""".strip()
    
    # Clean up the text
    comprehensive = re.sub(r'\s+', ' ', comprehensive)
    comprehensive = re.sub(r'\s+([.,;:])', r'\1', comprehensive)
    
    # Format into paragraphs
    sentences = comprehensive.split('.')
    formatted_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and len(sentence) > 5:
            formatted_sentences.append(sentence + '.')
    
    # Group into paragraphs
    para1 = " ".join(formatted_sentences[:3]) if len(formatted_sentences) >= 3 else " ".join(formatted_sentences)
    para2 = " ".join(formatted_sentences[3:6]) if len(formatted_sentences) > 3 else ""
    para3 = " ".join(formatted_sentences[6:]) if len(formatted_sentences) > 6 else ""
    
    print(para1)
    if para2:
        print(f"\n{para2}")
    if para3:
        print(f"\n{para3}")
    
    print(f"\n{'='*75}\n")
    
    return all_info, comprehensive

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python smart_analyze.py <image_path>")
        print("\nScript này hỏi nhiều câu hỏi chi tiết để thu thập đầy đủ thông tin")
        print("từ model Vintern-1B (workaround cho limitation generation ngắn)")
        sys.exit(1)
    
    smart_analyze(sys.argv[1])
