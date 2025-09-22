"""
Local Model Service cho Vintern-1B-v3.5
Chạy model trực tiếp trên máy thay vì qua HuggingFace API
"""

import os
import json
import torch
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
import logging

logger = logging.getLogger(__name__)

class LocalVinternModel:
    def __init__(self, model_path: str = None):
        self.model_path = model_path or self._get_model_path()
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForCausalLM] = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_loaded = False
        
    def _get_model_path(self) -> str:
        """Tìm model path từ config hoặc default location"""
        # Thử tìm trong thư mục models với tên git clone
        git_clone_path = Path(__file__).parent.parent.parent / "models" / "Vintern-1B-v3_5"
        if git_clone_path.exists():
            return str(git_clone_path)
            
        # Thử tìm trong thư mục models với tên cũ
        old_path = Path(__file__).parent.parent.parent / "models" / "vintern-1b-v3.5"
        if old_path.exists():
            return str(old_path)
        
        # Nếu không có, thử từ environment
        env_path = os.getenv("LOCAL_MODEL_PATH")
        if env_path:
            return env_path
            
        # Default fallback
        return str(git_clone_path)
    
    async def initialize(self) -> bool:
        """Load model và tokenizer"""
        try:
            logger.info(f"🚀 Đang load local model từ: {self.model_path}")
            logger.info(f"🔧 Device: {self.device}")
            
            # Kiểm tra model path tồn tại
            if not Path(self.model_path).exists():
                raise FileNotFoundError(f"Model path không tồn tại: {self.model_path}")
            
            # Load tokenizer
            logger.info("📥 Đang load tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # Load model
            logger.info("📥 Đang load model...")
            torch_dtype = torch.float16 if self.device == "cuda" else torch.float32
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                torch_dtype=torch_dtype,
                device_map="auto" if self.device == "cuda" else None,
                low_cpu_mem_usage=True
            )
            
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            
            # Set to eval mode
            self.model.eval()
            
            self.is_loaded = True
            logger.info("✅ Model được load thành công!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Lỗi khi load model: {e}")
            self.is_loaded = False
            return False
    
    def is_available(self) -> bool:
        """Kiểm tra model có sẵn sàng không"""
        return self.is_loaded and self.model is not None and self.tokenizer is not None
    
    async def generate_response(
        self, 
        prompt: str, 
        max_length: int = 512, 
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True
    ) -> str:
        """Generate response từ prompt"""
        if not self.is_available():
            raise RuntimeError("Model chưa được load hoặc không khả dụng")
        
        try:
            # Format prompt (có thể cần điều chỉnh theo format của Vintern)
            formatted_prompt = self._format_prompt(prompt)
            
            # Tokenize
            inputs = self.tokenizer(
                formatted_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=2048
            ).to(self.device)
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=do_sample,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"❌ Lỗi khi generate response: {e}")
            raise
    
    def _format_prompt(self, prompt: str) -> str:
        """Format prompt theo template của Vintern model"""
        # Template có thể cần điều chỉnh dựa trên documentation của model
        return f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    
    async def analyze_image_with_context(
        self, 
        image_description: str, 
        detected_objects: list = None,
        user_question: str = None
    ) -> str:
        """Phân tích ảnh với context từ object detection và câu hỏi của user"""
        
        # Tạo prompt comprehensive
        prompt_parts = [f"Phân tích ảnh này: {image_description}"]
        
        if detected_objects:
            objects_info = ", ".join([obj.get('name', 'unknown') for obj in detected_objects])
            prompt_parts.append(f"Các vật thể được phát hiện: {objects_info}")
        
        if user_question:
            prompt_parts.append(f"Câu hỏi cụ thể: {user_question}")
        
        prompt = "\n".join(prompt_parts)
        return await self.generate_response(prompt)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Lấy thông tin về model"""
        return {
            "model_path": self.model_path,
            "device": self.device,
            "is_loaded": self.is_loaded,
            "has_cuda": torch.cuda.is_available(),
            "model_name": "5CD-AI/Vintern-1B-v3_5"
        }

# Global instance
_local_model_instance: Optional[LocalVinternModel] = None

async def get_local_model() -> LocalVinternModel:
    """Get hoặc tạo local model instance"""
    global _local_model_instance
    
    if _local_model_instance is None:
        _local_model_instance = LocalVinternModel()
        await _local_model_instance.initialize()
    
    return _local_model_instance