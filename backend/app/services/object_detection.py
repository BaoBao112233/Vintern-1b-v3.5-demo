"""
Object Detection Service sử dụng YOLOv8
Phát hiện các vật thể trong ảnh và trả về bounding boxes
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from ultralytics import YOLO
import logging
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)

class ObjectDetector:
    def __init__(self, model_name: str = "yolov8n.pt"):
        self.model_name = model_name
        self.model: Optional[YOLO] = None
        self.is_loaded = False
        self.confidence_threshold = 0.5
        self.iou_threshold = 0.45
        
    async def initialize(self) -> bool:
        """Load YOLO model"""
        try:
            logger.info(f"🎯 Đang load YOLO model: {self.model_name}")
            
            # Load model (sẽ tự động download nếu chưa có)
            self.model = YOLO(self.model_name)
            self.is_loaded = True
            
            logger.info("✅ YOLO model loaded successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Lỗi khi load YOLO model: {e}")
            self.is_loaded = False
            return False
    
    def is_available(self) -> bool:
        """Kiểm tra model có sẵn sàng không"""
        return self.is_loaded and self.model is not None
    
    async def detect_objects(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect objects trong ảnh
        
        Args:
            image: numpy array của ảnh (BGR format)
            
        Returns:
            List of detected objects với format:
            {
                'name': str,
                'confidence': float,
                'bbox': [x1, y1, x2, y2],
                'center': [cx, cy],
                'area': float
            }
        """
        if not self.is_available():
            raise RuntimeError("Object detector chưa được load")
        
        try:
            # Run inference
            results = self.model(
                image,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                verbose=False
            )
            
            detected_objects = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get coordinates
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        confidence = box.conf[0].item()
                        class_id = int(box.cls[0].item())
                        class_name = self.model.names[class_id]
                        
                        # Calculate center and area
                        center_x = (x1 + x2) / 2
                        center_y = (y1 + y2) / 2
                        area = (x2 - x1) * (y2 - y1)
                        
                        detected_objects.append({
                            'name': class_name,
                            'confidence': confidence,
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'center': [int(center_x), int(center_y)],
                            'area': area,
                            'class_id': class_id
                        })
            
            return detected_objects
            
        except Exception as e:
            logger.error(f"❌ Lỗi khi detect objects: {e}")
            raise
    
    def draw_bounding_boxes(
        self, 
        image: np.ndarray, 
        objects: List[Dict[str, Any]]
    ) -> np.ndarray:
        """
        Vẽ bounding boxes lên ảnh
        
        Args:
            image: numpy array của ảnh
            objects: list detected objects
            
        Returns:
            ảnh với bounding boxes được vẽ
        """
        image_with_boxes = image.copy()
        
        for obj in objects:
            x1, y1, x2, y2 = obj['bbox']
            name = obj['name']
            confidence = obj['confidence']
            
            # Màu sắc cho bbox (BGR format)
            color = self._get_color_for_class(obj['class_id'])
            
            # Vẽ bounding box
            cv2.rectangle(image_with_boxes, (x1, y1), (x2, y2), color, 2)
            
            # Vẽ label
            label = f"{name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            
            # Background cho text
            cv2.rectangle(
                image_with_boxes,
                (x1, y1 - label_size[1] - 10),
                (x1 + label_size[0], y1),
                color,
                -1
            )
            
            # Text
            cv2.putText(
                image_with_boxes,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )
        
        return image_with_boxes
    
    def _get_color_for_class(self, class_id: int) -> Tuple[int, int, int]:
        """Tạo màu sắc cho từng class"""
        # Tạo màu sắc khác nhau cho mỗi class
        np.random.seed(class_id)
        return tuple(map(int, np.random.randint(0, 255, 3)))
    
    def get_objects_summary(self, objects: List[Dict[str, Any]]) -> str:
        """Tạo summary text về các objects được detect"""
        if not objects:
            return "Không phát hiện vật thể nào trong ảnh."
        
        # Đếm số lượng mỗi loại object
        object_counts = {}
        for obj in objects:
            name = obj['name']
            object_counts[name] = object_counts.get(name, 0) + 1
        
        # Tạo summary
        summary_parts = []
        summary_parts.append(f"Phát hiện {len(objects)} vật thể:")
        
        for name, count in object_counts.items():
            if count == 1:
                summary_parts.append(f"- 1 {name}")
            else:
                summary_parts.append(f"- {count} {name}")
        
        return "\n".join(summary_parts)
    
    def filter_objects_by_confidence(
        self, 
        objects: List[Dict[str, Any]], 
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Lọc objects theo confidence threshold"""
        return [obj for obj in objects if obj['confidence'] >= min_confidence]

# Global instance
_detector_instance: Optional[ObjectDetector] = None

async def get_object_detector() -> ObjectDetector:
    """Get hoặc tạo object detector instance"""
    global _detector_instance
    
    if _detector_instance is None:
        _detector_instance = ObjectDetector()
        await _detector_instance.initialize()
    
    return _detector_instance