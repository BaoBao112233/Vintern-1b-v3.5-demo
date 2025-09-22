#!/usr/bin/env python3
"""
Model Conversion Script for Vintern-1B
Converts Hugging Face model to GGUF format for llama.cpp
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import subprocess
import shutil
from huggingface_hub import snapshot_download
import tempfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_model(model_id: str, output_dir: str, token: str = None):
    """Download model from Hugging Face"""
    logger.info(f"Downloading model {model_id}...")
    
    try:
        model_path = snapshot_download(
            repo_id=model_id,
            cache_dir=output_dir,
            use_auth_token=token,
            ignore_patterns=["*.md", "*.txt", ".gitignore"]
        )
        logger.info(f"Model downloaded to: {model_path}")
        return model_path
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        raise

def convert_to_gguf(model_path: str, output_path: str, quantization: str = "q4_0"):
    """Convert model to GGUF format"""
    logger.info(f"Converting model to GGUF format with quantization {quantization}...")
    
    # Path to llama.cpp conversion scripts
    llama_cpp_path = os.getenv("LLAMA_CPP_PATH", "/app/llama.cpp")
    convert_script = os.path.join(llama_cpp_path, "convert.py")
    quantize_exec = os.path.join(llama_cpp_path, "quantize")
    
    if not os.path.exists(convert_script):
        raise FileNotFoundError(f"convert.py not found at {convert_script}")
    
    # Step 1: Convert to F16 GGUF
    f16_output = output_path.replace('.gguf', '_f16.gguf')
    
    cmd_convert = [
        "python3", convert_script,
        model_path,
        "--outfile", f16_output,
        "--outtype", "f16"
    ]
    
    logger.info(f"Running: {' '.join(cmd_convert)}")
    result = subprocess.run(cmd_convert, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"Conversion failed: {result.stderr}")
        raise RuntimeError(f"Model conversion failed: {result.stderr}")
    
    # Step 2: Quantize if requested
    if quantization != "f16":
        if not os.path.exists(quantize_exec):
            logger.warning(f"quantize executable not found at {quantize_exec}, skipping quantization")
            shutil.move(f16_output, output_path)
        else:
            cmd_quantize = [
                quantize_exec,
                f16_output,
                output_path,
                quantization.upper()
            ]
            
            logger.info(f"Running: {' '.join(cmd_quantize)}")
            result = subprocess.run(cmd_quantize, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Quantization failed: {result.stderr}")
                # Keep F16 version as fallback
                shutil.move(f16_output, output_path)
            else:
                # Remove F16 version
                os.remove(f16_output)
    else:
        shutil.move(f16_output, output_path)
    
    logger.info(f"Model converted successfully: {output_path}")

def create_config(model_path: str, output_dir: str):
    """Create configuration file for the model"""
    config = {
        "model_type": "gguf",
        "n_ctx": 4096,
        "n_threads": 4,
        "temperature": 0.1,
        "top_p": 0.9,
        "repeat_penalty": 1.1,
        "model_file": os.path.basename(model_path)
    }
    
    config_path = os.path.join(output_dir, "config.json")
    with open(config_path, 'w') as f:
        import json
        json.dump(config, f, indent=2)
    
    logger.info(f"Configuration saved to: {config_path}")

def main():
    parser = argparse.ArgumentParser(description="Convert Vintern-1B model to GGUF format")
    parser.add_argument("--model-id", default="5CD-AI/Vintern-1B-v3_5", 
                       help="Hugging Face model ID")
    parser.add_argument("--output-dir", default="/models",
                       help="Output directory for converted model")
    parser.add_argument("--quantization", default="q4_0",
                       choices=["f16", "q8_0", "q4_0", "q4_1", "q5_0", "q5_1", "q2_k", "q3_k", "q4_k", "q5_k", "q6_k"],
                       help="Quantization type")
    parser.add_argument("--token", 
                       help="Hugging Face API token")
    parser.add_argument("--download-only", action="store_true",
                       help="Only download, don't convert")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        # Download model
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = download_model(args.model_id, temp_dir, args.token)
            
            if args.download_only:
                # Copy to output directory
                shutil.copytree(model_path, os.path.join(args.output_dir, "original"))
                logger.info("Model downloaded successfully")
                return
            
            # Convert model
            output_filename = f"vintern-1b-v3_5-{args.quantization}.gguf"
            output_path = os.path.join(args.output_dir, output_filename)
            
            convert_to_gguf(model_path, output_path, args.quantization)
            
            # Create config
            create_config(output_path, args.output_dir)
            
            logger.info("Model conversion completed successfully!")
            logger.info(f"Model file: {output_path}")
            logger.info(f"Model size: {os.path.getsize(output_path) / (1024**3):.2f} GB")
            
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()