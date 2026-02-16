"""
Object Detection Service using YOLOv8-nano
Optimized for GTX 1050 Ti 4GB VRAM
Supports batch processing for multiple camera streams
"""

import os
import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DetectionService:
    """YOLOv8 Object Detection Service"""
    
    def __init__(
        self,
        model_name: str = "yolov8n.pt",
        conf_threshold: float = 0.5,
        device: str = "0",
        batch_size: int = 2
    ):
        """
        Initialize YOLO detection service
        
        Args:
            model_name: YOLO model file (e.g., 'yolov8n.pt')
            conf_threshold: Confidence threshold for detections
            device: Device to run on ('0' for GPU, 'cpu' for CPU)
            batch_size: Batch size for inference
        """
        self.model_name = model_name
        self.conf_threshold = conf_threshold
        self.device = device
        self.batch_size = batch_size
        self.model = None
        
        logger.info(f"Initializing Detection Service:")
        logger.info(f"  Model: {model_name}")
        logger.info(f"  Device: {device}")
        logger.info(f"  Conf threshold: {conf_threshold}")
        logger.info(f"  Batch size: {batch_size}")
        
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model"""
        try:
            # Import ultralytics (will auto-install if needed)
            try:
                from ultralytics import YOLO
                logger.info("✅ ultralytics library available")
            except ImportError:
                logger.info("📦 Installing ultralytics...")
                import subprocess
                import sys
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", 
                    "ultralytics", "-q"
                ])
                from ultralytics import YOLO
                logger.info("✅ ultralytics installed")
            
            # Load model
            logger.info(f"Loading model: {self.model_name}")
            self.model = YOLO(self.model_name)
            
            # Log device info
            if self.device != "cpu":
                logger.info(f"Using device: GPU {self.device}")
            else:
                logger.info(f"Using device: CPU")
            
            # Test inference
            logger.info("Running warmup inference...")
            dummy_image = np.zeros((640, 640, 3), dtype=np.uint8)
            _ = self.model.predict(
                dummy_image, 
                device=self.device,
                verbose=False,
                conf=self.conf_threshold
            )
            
            logger.info("✅ Model loaded and ready")
            
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise
    
    def detect(
        self, 
        images: List[np.ndarray],
        return_crops: bool = False
    ) -> List[Dict]:
        """
        Detect objects in images
        
        Args:
            images: List of images (numpy arrays in RGB format)
            return_crops: If True, return cropped object images
        
        Returns:
            List of detection results, one dict per image:
            {
                'boxes': [[x1, y1, x2, y2], ...],
                'scores': [conf1, conf2, ...],
                'classes': [cls1, cls2, ...],
                'class_names': ['person', 'car', ...],
                'crops': [crop1, crop2, ...] (if return_crops=True)
            }
        """
        if not images:
            return []
        
        try:
            # Batch inference
            results = self.model.predict(
                images,
                device=self.device,
                verbose=False,
                conf=self.conf_threshold,
                batch=min(len(images), self.batch_size)
            )
            
            # Parse results
            detections_list = []
            
            for idx, result in enumerate(results):
                boxes = result.boxes
                
                detection_dict = {
                    'boxes': [],
                    'scores': [],
                    'classes': [],
                    'class_names': [],
                    'crops': [] if return_crops else None,
                    'image_shape': images[idx].shape
                }
                
                if len(boxes) > 0:
                    # Extract data
                    detection_dict['boxes'] = boxes.xyxy.cpu().numpy().tolist()
                    detection_dict['scores'] = boxes.conf.cpu().numpy().tolist()
                    detection_dict['classes'] = boxes.cls.cpu().numpy().astype(int).tolist()
                    
                    # Get class names
                    detection_dict['class_names'] = [
                        self.model.names[int(cls)] 
                        for cls in detection_dict['classes']
                    ]
                    
                    # Extract crops if requested
                    if return_crops:
                        image = images[idx]
                        for box in detection_dict['boxes']:
                            x1, y1, x2, y2 = map(int, box)
                            crop = image[y1:y2, x1:x2]
                            detection_dict['crops'].append(crop)
                
                detections_list.append(detection_dict)
            
            return detections_list
            
        except Exception as e:
            logger.error(f"❌ Detection failed: {e}")
            return [{'boxes': [], 'scores': [], 'classes': [], 'class_names': []} 
                    for _ in images]
    
    def detect_single(
        self, 
        image: np.ndarray,
        return_crops: bool = False
    ) -> Dict:
        """
        Detect objects in a single image
        
        Args:
            image: Image as numpy array (RGB format)
            return_crops: If True, return cropped object images
        
        Returns:
            Detection result dict
        """
        results = self.detect([image], return_crops=return_crops)
        return results[0] if results else {
            'boxes': [], 'scores': [], 'classes': [], 'class_names': []
        }
    
    def get_summary(self, detection: Dict) -> str:
        """
        Get human-readable summary of detections
        
        Args:
            detection: Detection dict from detect() or detect_single()
        
        Returns:
            Summary string
        """
        if not detection['class_names']:
            return "No objects detected"
        
        # Count objects by class
        from collections import Counter
        class_counts = Counter(detection['class_names'])
        
        # Format summary
        items = []
        for cls, count in class_counts.most_common():
            items.append(f"{count} {cls}{'s' if count > 1 else ''}")
        
        return "Detected: " + ", ".join(items)
    
    def __del__(self):
        """Cleanup"""
        if self.model is not None:
            del self.model
            logger.info("Detection model unloaded")


def test_detection():
    """Test detection service"""
    logger.info("=" * 60)
    logger.info("Testing Detection Service")
    logger.info("=" * 60)
    
    # Initialize service
    detector = DetectionService(
        model_name="yolov8n.pt",
        conf_threshold=0.5,
        device="0",  # GPU
        batch_size=2
    )
    
    # Create test images
    logger.info("\n📸 Creating test images...")
    test_images = [
        np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8),
        np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    ]
    
    # Test single detection
    logger.info("\n🔍 Testing single image detection...")
    result = detector.detect_single(test_images[0])
    logger.info(f"Result: {detector.get_summary(result)}")
    
    # Test batch detection
    logger.info("\n🔍 Testing batch detection (2 images)...")
    results = detector.detect(test_images)
    for idx, result in enumerate(results):
        logger.info(f"Image {idx + 1}: {detector.get_summary(result)}")
    
    logger.info("\n✅ Detection service test complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    test_detection()
