#!/usr/bin/env python3
"""
Enhanced Model Downloader for Vintern-1B v3.5
Uses HuggingFace Hub API for efficient downloads
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime

def download_model():
    """Download Vintern-1B v3.5 model from HuggingFace"""
    
    model_repo = "5CD-AI/Vintern-1B-v3_5"
    project_root = Path(__file__).parent.parent
    models_dir = project_root / "models"
    model_dir = models_dir / "Vintern-1B-v3_5"
    
    print("=" * 70)
    print("🤖 VINTERN-1B v3.5 MODEL DOWNLOADER")
    print("=" * 70)
    print(f"📦 Repository: {model_repo}")
    print(f"📁 Target dir:  {model_dir}")
    print("=" * 70)
    
    # Create models directory
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if model exists
    if model_dir.exists():
        config_file = model_dir / "config.json"
        if config_file.exists():
            print(f"\n✅ Model already exists at {model_dir}")
            
            # Verify essential files
            essential_files = [
                "config.json",
                "tokenizer_config.json", 
                "generation_config.json"
            ]
            
            missing = []
            for f in essential_files:
                if not (model_dir / f).exists():
                    missing.append(f)
            
            if missing:
                print(f"⚠️  Missing files: {missing}")
                print("🔄 Re-downloading...")
            else:
                print("✅ All essential files present")
                print(f"\n📊 Model size: ", end="")
                
                # Calculate size
                total_size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
                size_gb = total_size / (1024**3)
                print(f"{size_gb:.2f} GB")
                
                return str(model_dir)
    
    # Install huggingface_hub if needed
    try:
        from huggingface_hub import snapshot_download
        print("\n✅ huggingface_hub available")
    except ImportError:
        print("\n📦 Installing huggingface_hub...")
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "huggingface_hub"],
            capture_output=True
        )
        if result.returncode != 0:
            print(f"❌ Failed to install: {result.stderr.decode()}")
            sys.exit(1)
        
        from huggingface_hub import snapshot_download
        print("✅ huggingface_hub installed")
    
    # Download model
    print(f"\n📥 Downloading model from HuggingFace...")
    print("⏱️  This may take 5-15 minutes depending on connection")
    print("💾 Expected size: ~2-4 GB\n")
    
    try:
        downloaded_path = snapshot_download(
            repo_id=model_repo,
            local_dir=str(model_dir),
            local_dir_use_symlinks=False,
            resume_download=True,
            ignore_patterns=["*.git*", "*.md", ".gitattributes"]
        )
        
        print(f"\n✅ Download complete!")
        print(f"📂 Model saved to: {downloaded_path}")
        
        # Verify download
        essential_files = {
            "config.json": "Model configuration",
            "tokenizer_config.json": "Tokenizer config",
            "generation_config.json": "Generation config"
        }
        
        print(f"\n🔍 Verifying downloaded files:")
        all_ok = True
        for fname, desc in essential_files.items():
            path = model_dir / fname
            if path.exists():
                size_kb = path.stat().st_size / 1024
                print(f"   ✅ {fname:30s} ({size_kb:,.1f} KB) - {desc}")
            else:
                print(f"   ❌ {fname:30s} - MISSING!")
                all_ok = False
        
        # Check for model weights
        weight_files = list(model_dir.glob("*.bin")) + list(model_dir.glob("*.safetensors"))
        if weight_files:
            total_weight_size = sum(f.stat().st_size for f in weight_files) / (1024**3)
            print(f"   ✅ Model weights: {len(weight_files)} file(s), {total_weight_size:.2f} GB")
        else:
            print(f"   ⚠️  No model weight files found (.bin or .safetensors)")
            all_ok = False
        
        if not all_ok:
            print("\n⚠️  Download may be incomplete!")
            sys.exit(1)
        
        # Save download metadata
        metadata = {
            "repo_id": model_repo,
            "local_path": str(model_dir),
            "downloaded_at": datetime.now().isoformat(),
            "download_method": "huggingface_hub",
            "files_count": len(list(model_dir.rglob("*"))),
            "total_size_gb": sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file()) / (1024**3)
        }
        
        metadata_path = model_dir / "download_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n✅ Model ready for use!")
        print(f"📊 Total size: {metadata['total_size_gb']:.2f} GB")
        print(f"📄 Files: {metadata['files_count']}")
        
        return str(model_dir)
        
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check internet connection")
        print("   2. Verify HuggingFace access")
        print("   3. Try: pip install -U huggingface_hub")
        print("   4. Manual download: https://huggingface.co/5CD-AI/Vintern-1B-v3_5")
        sys.exit(1)

def main():
    """Main entry point"""
    try:
        model_path = download_model()
        
        print("\n" + "=" * 70)
        print("🎉 SUCCESS!")
        print("=" * 70)
        print(f"✅ Model location: {model_path}")
        print(f"🔧 Use in .env: VLLM_MODEL_PATH=/models/Vintern-1B-v3_5")
        print("=" * 70)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Download cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
