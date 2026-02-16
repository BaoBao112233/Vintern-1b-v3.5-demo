#!/usr/bin/env python3
"""
Example Vision Service cho Raspberry Pi Backend
Ready-to-use service có thể integrate trực tiếp vào FastAPI
"""

from pc_inference_client import PCInferenceClient
from PIL import Image
import io
import time
import logging
from typing import Optional, List, Dict, Union

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VisionAIService:
    """
    Service wrapper cho Vision AI inference từ PC
    
    Features:
    - Simple single-turn analysis
    - Detailed multi-turn comprehensive analysis
    - Context management
    - Error handling & retry logic
    - Performance monitoring
    """
    
    def __init__(
        self,
        pc_host: str = "192.168.1.3",
        pc_port: int = 8080,
        timeout: int = 60,
        max_retries: int = 2
    ):
        """
        Initialize Vision AI Service
        
        Args:
            pc_host: PC inference server IP
            pc_port: PC inference server port
            timeout: Request timeout in seconds
            max_retries: Max retry attempts
        """
        self.client = PCInferenceClient(
            host=pc_host,
            port=pc_port,
            timeout=timeout,
            max_retries=max_retries
        )
        
        # Multi-phase analysis questions (như smart_analyze.py)
        self.comprehensive_questions = {
            "overview": [
                "Bạn thấy gì trong ảnh này? Mô tả ngắn gọn."
            ],
            "objects": [
                "Có những loại vật thể gì? Liệt kê cụ thể.",
                "Có bao nhiêu vật thể? Đếm từng loại.",
            ],
            "details": [
                "Màu sắc của các vật thể như thế nào?",
                "Vật thể được sắp xếp như thế nào?"
            ],
            "context": [
                "Nền của ảnh là gì?",
                "Có yếu tố nào khác đáng chú ý không?"
            ]
        }
        
        logger.info(f"VisionAIService initialized: {pc_host}:{pc_port}")
    
    def health_check(self) -> bool:
        """
        Kiểm tra PC server có available không
        
        Returns:
            bool: True nếu server OK
        """
        try:
            status = self.client.health_check()
            return status.get("status") == "ok"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def analyze_simple(
        self,
        image: Union[Image.Image, bytes],
        custom_prompt: Optional[str] = None
    ) -> Dict:
        """
        Phân tích đơn giản với 1 câu hỏi
        
        Args:
            image: PIL Image hoặc bytes
            custom_prompt: Custom prompt (optional)
            
        Returns:
            {
                "description": str,
                "tokens": int,
                "latency_ms": float,
                "success": bool
            }
        """
        start_time = time.time()
        
        try:
            # Convert bytes to PIL if needed
            if isinstance(image, bytes):
                image = Image.open(io.BytesIO(image))
            
            # Default prompt
            prompt = custom_prompt or "Mô tả những gì bạn thấy trong ảnh."
            
            # Single turn inference
            result = self.client.chat_completion(
                image=image,
                prompt=prompt
            )
            
            latency = (time.time() - start_time) * 1000
            
            logger.info(f"Simple analysis completed: {latency:.2f}ms")
            
            return {
                "description": result.get("content", ""),
                "tokens": result.get("tokens", 0),
                "latency_ms": round(latency, 2),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Simple analysis failed: {e}")
            return {
                "description": "",
                "tokens": 0,
                "latency_ms": 0,
                "success": False,
                "error": str(e)
            }
    
    def analyze_comprehensive(
        self,
        image: Union[Image.Image, bytes],
        custom_phases: Optional[Dict[str, List[str]]] = None
    ) -> Dict:
        """
        Phân tích toàn diện với multi-turn conversation
        
        Args:
            image: PIL Image hoặc bytes
            custom_phases: Custom question phases (optional)
            
        Returns:
            {
                "summary": str,              # Tổng hợp tất cả câu trả lời
                "phases": {...},             # Chi tiết từng phase
                "total_tokens": int,
                "total_time_ms": float,
                "success": bool
            }
        """
        start_time = time.time()
        
        try:
            # Convert bytes to PIL if needed
            if isinstance(image, bytes):
                image = Image.open(io.BytesIO(image))
            
            # Use custom phases or default
            phases = custom_phases or self.comprehensive_questions
            
            results = {}
            total_tokens = 0
            conversation_context = []
            
            # Loop qua từng phase
            for phase_name, questions in phases.items():
                phase_answers = []
                
                for i, question in enumerate(questions):
                    # First question includes image, rest use context
                    if not conversation_context:
                        result = self.client.chat_completion(
                            image=image,
                            prompt=question
                        )
                    else:
                        # Multi-turn: reuse context
                        result = self.client.chat_completion(
                            image=None,  # No image for follow-ups
                            prompt=question,
                            context=conversation_context
                        )
                    
                    answer = result.get("content", "")
                    phase_answers.append(answer)
                    total_tokens += result.get("tokens", 0)
                    
                    # Update context for next turn
                    conversation_context = result.get("context", [])
                    
                    logger.debug(f"Phase {phase_name} Q{i+1}: {len(answer)} chars")
                
                # Join all answers in this phase
                results[phase_name] = " ".join(phase_answers)
            
            # Generate comprehensive summary
            summary_parts = []
            for phase_name, content in results.items():
                if content.strip():
                    summary_parts.append(content.strip())
            
            summary = " ".join(summary_parts)
            summary = " ".join(summary.split())  # Clean whitespace
            
            total_time = (time.time() - start_time) * 1000
            
            logger.info(
                f"Comprehensive analysis completed: "
                f"{total_tokens} tokens, {total_time:.2f}ms"
            )
            
            return {
                "summary": summary,
                "phases": results,
                "total_tokens": total_tokens,
                "total_time_ms": round(total_time, 2),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")
            return {
                "summary": "",
                "phases": {},
                "total_tokens": 0,
                "total_time_ms": 0,
                "success": False,
                "error": str(e)
            }
    
    def analyze_with_yolo(
        self,
        image: Union[Image.Image, bytes],
        yolo_detections: List[Dict]
    ) -> Dict:
        """
        Phân tích kết hợp YOLO detection results
        
        Args:
            image: PIL Image hoặc bytes
            yolo_detections: List of YOLO boxes, e.g.:
                [
                    {"label": "person", "confidence": 0.95, "bbox": [...]},
                    {"label": "car", "confidence": 0.88, "bbox": [...]}
                ]
                
        Returns:
            {
                "vlm_description": str,      # VLM mô tả
                "yolo_detections": [...],    # Original YOLO results
                "verification": str,         # VLM verify YOLO
                "confidence": float,         # Combined confidence
                "success": bool
            }
        """
        start_time = time.time()
        
        try:
            # Convert bytes to PIL if needed
            if isinstance(image, bytes):
                image = Image.open(io.BytesIO(image))
            
            # Extract labels from YOLO
            detected_labels = [d['label'] for d in yolo_detections]
            
            if detected_labels:
                # Ask VLM to verify what YOLO found
                verify_prompt = (
                    f"Hệ thống phát hiện các đối tượng: {', '.join(detected_labels)}. "
                    f"Bạn có thấy những đối tượng này trong ảnh không? "
                    f"Xác nhận và mô tả chi tiết vị trí, màu sắc của chúng."
                )
            else:
                verify_prompt = "Mô tả chi tiết những gì bạn thấy trong ảnh."
            
            # Get VLM response
            result = self.client.chat_completion(
                image=image,
                prompt=verify_prompt
            )
            
            vlm_description = result.get("content", "")
            
            # Calculate confidence (simple keyword matching)
            confidence = self._calculate_confidence(
                detected_labels,
                vlm_description
            )
            
            latency = (time.time() - start_time) * 1000
            
            logger.info(
                f"YOLO+VLM analysis: {len(detected_labels)} objects, "
                f"confidence={confidence:.2f}, {latency:.2f}ms"
            )
            
            return {
                "vlm_description": vlm_description,
                "yolo_detections": yolo_detections,
                "verification": "confirmed" if confidence > 0.7 else "uncertain",
                "confidence": confidence,
                "tokens": result.get("tokens", 0),
                "latency_ms": round(latency, 2),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"YOLO+VLM analysis failed: {e}")
            return {
                "vlm_description": "",
                "yolo_detections": yolo_detections,
                "verification": "error",
                "confidence": 0.0,
                "success": False,
                "error": str(e)
            }
    
    def _calculate_confidence(
        self,
        yolo_labels: List[str],
        vlm_text: str
    ) -> float:
        """
        Calculate confidence score by matching YOLO labels với VLM text
        
        Returns:
            float: 0.0 to 1.0
        """
        if not yolo_labels:
            return 0.5  # No YOLO detections
        
        vlm_lower = vlm_text.lower()
        
        # Count how many YOLO labels appear in VLM description
        matches = sum(1 for label in yolo_labels if label.lower() in vlm_lower)
        
        # Base confidence + bonus for matches
        base_confidence = 0.5
        match_bonus = (matches / len(yolo_labels)) * 0.5
        
        return min(base_confidence + match_bonus, 1.0)


# ============================================================================
# Usage Examples
# ============================================================================

def example_simple_analysis():
    """Example: Simple single-turn analysis"""
    
    service = VisionAIService(pc_host="192.168.1.3", pc_port=8080)
    
    # Check connection
    if not service.health_check():
        print("❌ PC server not available!")
        return
    
    # Analyze an image
    image = Image.open("test.jpg")
    result = service.analyze_simple(image)
    
    if result["success"]:
        print(f"✅ Description: {result['description']}")
        print(f"📊 Tokens: {result['tokens']}, Latency: {result['latency_ms']}ms")
    else:
        print(f"❌ Error: {result.get('error')}")


def example_comprehensive_analysis():
    """Example: Comprehensive multi-turn analysis"""
    
    service = VisionAIService(pc_host="192.168.1.3", pc_port=8080)
    
    image = Image.open("test.jpg")
    result = service.analyze_comprehensive(image)
    
    if result["success"]:
        print("✅ COMPREHENSIVE ANALYSIS")
        print(f"\n📝 Summary:\n{result['summary']}\n")
        print(f"📊 Tokens: {result['total_tokens']}")
        print(f"⏱️  Time: {result['total_time_ms']}ms")
        
        print("\n📋 Phase Details:")
        for phase, content in result['phases'].items():
            print(f"  • {phase}: {content[:100]}...")
    else:
        print(f"❌ Error: {result.get('error')}")


def example_yolo_integration():
    """Example: Integration with YOLO detections"""
    
    service = VisionAIService(pc_host="192.168.1.3", pc_port=8080)
    
    # Mock YOLO results
    yolo_results = [
        {"label": "person", "confidence": 0.95, "bbox": [100, 150, 300, 450]},
        {"label": "car", "confidence": 0.88, "bbox": [400, 200, 700, 500]}
    ]
    
    image = Image.open("test.jpg")
    result = service.analyze_with_yolo(image, yolo_results)
    
    if result["success"]:
        print(f"✅ VLM Description: {result['vlm_description']}")
        print(f"🔍 Verification: {result['verification']}")
        print(f"📊 Confidence: {result['confidence']:.2%}")
    else:
        print(f"❌ Error: {result.get('error')}")


if __name__ == "__main__":
    print("🎯 Vision AI Service Examples\n")
    print("=" * 70)
    
    # Run examples
    print("\n1️⃣  Simple Analysis:")
    example_simple_analysis()
    
    print("\n" + "=" * 70)
    print("\n2️⃣  Comprehensive Analysis:")
    example_comprehensive_analysis()
    
    print("\n" + "=" * 70)
    print("\n3️⃣  YOLO Integration:")
    example_yolo_integration()
