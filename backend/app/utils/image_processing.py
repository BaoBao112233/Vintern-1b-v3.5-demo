"""
Image processing utilities
"""
import base64
import logging
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

logger = logging.getLogger(__name__)

def process_image(
    image: Image.Image, 
    target_width: int = 640, 
    target_height: int = 480,
    maintain_aspect_ratio: bool = True
) -> Image.Image:
    """
    Process and resize image for model inference
    
    Args:
        image: Input PIL Image
        target_width: Target width
        target_height: Target height
        maintain_aspect_ratio: Whether to maintain aspect ratio
        
    Returns:
        Processed PIL Image
    """
    try:
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        original_width, original_height = image.size
        logger.debug(f"Original image size: {original_width}x{original_height}")
        
        if maintain_aspect_ratio:
            # Calculate new size maintaining aspect ratio
            aspect_ratio = original_width / original_height
            
            if aspect_ratio > target_width / target_height:
                # Image is wider - fit to width
                new_width = target_width
                new_height = int(target_width / aspect_ratio)
            else:
                # Image is taller - fit to height
                new_height = target_height
                new_width = int(target_height * aspect_ratio)
            
            # Resize image
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create canvas with target size and paste resized image
            processed_image = Image.new('RGB', (target_width, target_height), (0, 0, 0))
            
            # Calculate position to center the image
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            
            processed_image.paste(resized_image, (x_offset, y_offset))
            
        else:
            # Direct resize without maintaining aspect ratio
            processed_image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        logger.debug(f"Processed image size: {processed_image.size}")
        return processed_image
        
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        raise

def encode_result_image(image: Image.Image, format: str = 'JPEG', quality: int = 85) -> str:
    """
    Encode PIL Image to base64 string
    
    Args:
        image: PIL Image to encode
        format: Image format (JPEG, PNG)
        quality: JPEG quality (1-100)
        
    Returns:
        Base64 encoded string
    """
    try:
        buffer = BytesIO()
        
        # Save image to buffer
        if format.upper() == 'JPEG':
            # Ensure RGB mode for JPEG
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image.save(buffer, format=format, quality=quality, optimize=True)
        else:
            image.save(buffer, format=format)
        
        # Get base64 string
        buffer.seek(0)
        image_bytes = buffer.getvalue()
        base64_string = base64.b64encode(image_bytes).decode('utf-8')
        
        return base64_string
        
    except Exception as e:
        logger.error(f"Image encoding error: {e}")
        raise

def decode_base64_image(base64_string: str) -> Image.Image:
    """
    Decode base64 string to PIL Image
    
    Args:
        base64_string: Base64 encoded image string
        
    Returns:
        PIL Image object
    """
    try:
        # Remove data URL prefix if present
        if base64_string.startswith('data:image'):
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        image_bytes = base64.b64decode(base64_string)
        
        # Create PIL Image
        image = Image.open(BytesIO(image_bytes))
        
        return image
        
    except Exception as e:
        logger.error(f"Image decoding error: {e}")
        raise

def create_annotated_image(
    image: Image.Image, 
    detections: list,
    font_size: int = 12,
    box_color: str = "red",
    text_color: str = "red"
) -> Image.Image:
    """
    Create annotated image with bounding boxes and labels
    
    Args:
        image: Original PIL Image
        detections: List of detection results
        font_size: Font size for labels
        box_color: Color for bounding boxes
        text_color: Color for text labels
        
    Returns:
        Annotated PIL Image
    """
    try:
        # Create a copy of the original image
        annotated = image.copy()
        draw = ImageDraw.Draw(annotated)
        
        # Try to load a font
        try:
            # Common font paths on different systems
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/System/Library/Fonts/Arial.ttf",  # macOS
                "C:/Windows/Fonts/arial.ttf",  # Windows
            ]
            
            font = None
            for font_path in font_paths:
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except:
                    continue
            
            if font is None:
                font = ImageFont.load_default()
                
        except Exception as e:
            logger.warning(f"Could not load font: {e}")
            font = ImageFont.load_default()
        
        # Draw detections
        for detection in detections:
            try:
                # Extract detection info
                label = detection.get("label", "unknown")
                confidence = detection.get("confidence", 0.0)
                bbox = detection.get("bbox", {})
                
                # Skip if no bbox
                if not bbox:
                    continue
                
                # Handle different bbox formats
                if "xmin" in bbox and "ymin" in bbox:
                    # Format: {"xmin": x1, "ymin": y1, "xmax": x2, "ymax": y2}
                    x1, y1, x2, y2 = bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"]
                elif "x" in bbox and "y" in bbox:
                    # Format: {"x": x1, "y": y1, "width": w, "height": h}
                    x1, y1 = bbox["x"], bbox["y"]
                    x2, y2 = x1 + bbox.get("width", 0), y1 + bbox.get("height", 0)
                elif len(bbox) == 4:
                    # Format: [x1, y1, x2, y2] or [x1, y1, width, height]
                    if isinstance(bbox, (list, tuple)):
                        x1, y1, x2, y2 = bbox
                    else:
                        continue
                else:
                    continue
                
                # Ensure coordinates are within image bounds
                img_width, img_height = image.size
                x1 = max(0, min(x1, img_width))
                y1 = max(0, min(y1, img_height))
                x2 = max(0, min(x2, img_width))
                y2 = max(0, min(y2, img_height))
                
                # Draw bounding box
                draw.rectangle([x1, y1, x2, y2], outline=box_color, width=2)
                
                # Draw label with confidence
                if confidence > 0:
                    label_text = f"{label} ({confidence:.2f})"
                else:
                    label_text = label
                
                # Calculate text position
                text_x = x1
                text_y = y1 - font_size - 2
                if text_y < 0:
                    text_y = y1 + 2
                
                # Draw text background
                try:
                    # Get text bounding box
                    bbox_text = draw.textbbox((text_x, text_y), label_text, font=font)
                    draw.rectangle(bbox_text, fill="black", outline=text_color)
                except:
                    # Fallback if textbbox is not available
                    pass
                
                # Draw text
                draw.text((text_x, text_y), label_text, fill=text_color, font=font)
                
            except Exception as e:
                logger.warning(f"Error drawing detection: {e}")
                continue
        
        return annotated
        
    except Exception as e:
        logger.error(f"Error creating annotated image: {e}")
        return image  # Return original if annotation fails

def image_to_numpy(image: Image.Image) -> np.ndarray:
    """
    Convert PIL Image to numpy array
    
    Args:
        image: PIL Image
        
    Returns:
        Numpy array in RGB format
    """
    try:
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array
        np_array = np.array(image)
        
        return np_array
        
    except Exception as e:
        logger.error(f"Image to numpy conversion error: {e}")
        raise

def numpy_to_image(np_array: np.ndarray) -> Image.Image:
    """
    Convert numpy array to PIL Image
    
    Args:
        np_array: Numpy array
        
    Returns:
        PIL Image
    """
    try:
        # Ensure array is in the correct format
        if np_array.dtype != np.uint8:
            np_array = np_array.astype(np.uint8)
        
        # Handle different array shapes
        if len(np_array.shape) == 3:
            # RGB or BGR image
            if np_array.shape[2] == 3:
                # Convert BGR to RGB if needed (OpenCV uses BGR by default)
                if np_array.shape[2] == 3:
                    image = Image.fromarray(np_array, 'RGB')
            elif np_array.shape[2] == 4:
                # RGBA image
                image = Image.fromarray(np_array, 'RGBA')
            else:
                raise ValueError(f"Unsupported number of channels: {np_array.shape[2]}")
        elif len(np_array.shape) == 2:
            # Grayscale image
            image = Image.fromarray(np_array, 'L')
        else:
            raise ValueError(f"Unsupported array shape: {np_array.shape}")
        
        return image
        
    except Exception as e:
        logger.error(f"Numpy to image conversion error: {e}")
        raise