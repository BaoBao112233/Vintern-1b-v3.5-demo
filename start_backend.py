#!/usr/bin/env python3
"""
Production backend runner without vLLM (since it's not ready)
Mock VLM client to avoid errors
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Mock VLM client since vLLM is not running
import sys
sys.path.insert(0, 'backend')

# Create mock VLM client
mock_vlm_code = '''
import logging
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

class VLMClient:
    """Mock VLM Client (vLLM not running)"""
    
    def __init__(self, api_url: str, **kwargs):
        self.api_url = api_url
        logger.info(f"🧠 VLM Client initialized (MOCK MODE)")
        logger.info(f"   API URL: {api_url} (not used)")
    
    def check_health(self) -> bool:
        """Always return False since vLLM not running"""
        return False
    
    def analyze(self, image: np.ndarray, prompt: str, **kwargs) -> str:
        """Return mock analysis"""
        return "VLM analysis not available (vLLM server not running)"
    
    def analyze_text_only(self, prompt: str) -> str:
        """Return mock text response"""
        return "VLM not available"
'''

# Write mock VLM client
vlm_mock_path = Path('backend/app/services/vlm_client_mock.py')
vlm_mock_path.write_text(mock_vlm_code)

# Patch imports
import importlib.util
spec = importlib.util.spec_from_file_location("vlm_client", vlm_mock_path)
vlm_module = importlib.util.module_from_spec(spec)
sys.modules['app.services.vlm_client'] = vlm_module
spec.loader.exec_module(vlm_module)

# Now run server
if __name__ == "__main__":
    import uvicorn
    from app.main_production import app
    
    host = os.getenv('BACKEND_HOST', '0.0.0.0')
    port = int(os.getenv('BACKEND_PORT', '8001'))
    
    print("=" * 70)
    print("🚀 VINTERN VISION AI - BACKEND SERVER")
    print("=" * 70)
    print(f"📡 API:       http://{host}:{port}")
    print(f"🔌 WebSocket: ws://{host}:{port}/ws")
    print(f"📹 Cameras:   2 x RTSP @ 1 FPS")
    print(f"🔍 Detection: YOLOv8-nano (CPU)")
    print(f"🧠 VLM:       MOCK MODE (vLLM not running)")
    print("=" * 70)
    print()
    
    uvicorn.run(
        "app.main_production:app",
        host=host,
        port=port,
        log_level="info",
        reload=False
    )
