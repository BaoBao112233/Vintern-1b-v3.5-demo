#!/usr/bin/env python3
"""
Download and prepare Vintern-1B-v3.5 model for VLLM service
"""

import os
import sys
from pathlib import Path
from huggingface_hub import snapshot_download

def download_model():
    """Download model from HuggingFace"""
    model_name = "5CD-AI/Vintern-1B-v3_5"
    local_dir = "models/Vintern-1B-v3_5"
    
    print(f"📥 Downloading {model_name}...")
    print(f"📂 Saving to: {local_dir}")
    
    try:
        snapshot_download(
            repo_id=model_name,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            resume_download=True
        )
        
        print("✅ Model downloaded successfully!")
        print(f"📁 Model location: {Path(local_dir).absolute()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

if __name__ == "__main__":
    success = download_model()
    sys.exit(0 if success else 1)
