#!/usr/bin/env python3
"""
Script để download model Vintern-1B-v3.5 từ HuggingFace về local
Sử dụng git clone để tải model trực tiếp
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil

def download_model():
    """Download model từ HuggingFace sử dụng git clone"""
    model_repo = "https://huggingface.co/5CD-AI/Vintern-1B-v3_5"
    models_dir = Path(__file__).parent / "models"
    model_dir = models_dir / "Vintern-1B-v3_5"  # Tên chính xác của repo
    
    print(f"🚀 Đang tải model từ {model_repo}...")
    print(f"📁 Sẽ lưu vào: {model_dir}")
    
    # Tạo thư mục nếu chưa có
    models_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Kiểm tra git
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Git không được cài đặt. Vui lòng cài đặt Git trước.")
            sys.exit(1)
        
        # Xóa thư mục cũ nếu có
        if model_dir.exists():
            print(f"� Xóa model cũ tại {model_dir}")
            shutil.rmtree(model_dir)
        
        # Clone repository
        print("📥 Đang clone model repository...")
        result = subprocess.run([
            "git", "clone", 
            model_repo,
            str(model_dir)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Lỗi khi clone repository:")
            print(result.stderr)
            sys.exit(1)
        
        print("✅ Model đã được tải thành công!")
        
        # Kiểm tra các file quan trọng
        important_files = ["config.json", "pytorch_model.bin", "tokenizer.json"]
        missing_files = []
        
        for file in important_files:
            if not (model_dir / file).exists():
                missing_files.append(file)
        
        if missing_files:
            print(f"⚠️  Cảnh báo: Một số file quan trọng có thể bị thiếu: {missing_files}")
        else:
            print("✅ Tất cả file model quan trọng đã được tải")
        
        # Tạo config file
        config_path = model_dir / "download_info.json"
        config = {
            "model_repo": model_repo,
            "model_path": str(model_dir),
            "download_method": "git_clone",
            "downloaded_at": str(__import__('datetime').datetime.now())
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Tải model hoàn thành!")
        print(f"📂 Model được lưu tại: {model_dir}")
        print(f"🔧 Sử dụng với MODEL_MODE=local")
        
        return str(model_dir)
        
    except Exception as e:
        print(f"❌ Lỗi khi tải model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 VINTERN MODEL DOWNLOADER")
    print("=" * 50)
    
    model_path = download_model()
    
    print("=" * 50)
    print("🎉 DOWNLOAD HOÀN THÀNH!")
    print(f"Model path: {model_path}")
    print("Bạn có thể chạy backend với MODEL_MODE=local")
    print("=" * 50)