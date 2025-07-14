import cv2
import numpy as np
from PIL import Image, ImageEnhance
import os
import logging

logger = logging.getLogger(__name__)

def preprocess_image(image):
    """Preprocess image for better face recognition"""
    try:
        # Convert to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            # Assuming BGR input from OpenCV
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image for easier processing
        pil_image = Image.fromarray(image)
        
        # Enhance image quality
        enhancer = ImageEnhance.Sharpness(pil_image)
        pil_image = enhancer.enhance(1.2)
        
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(1.1)
        
        # Convert back to numpy array
        processed_image = np.array(pil_image)
        
        # Convert back to BGR for OpenCV
        if len(processed_image.shape) == 3:
            processed_image = cv2.cvtColor(processed_image, cv2.COLOR_RGB2BGR)
        
        return processed_image
        
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        return image

def validate_face_image(image_path):
    """Validate if image is suitable for face recognition"""
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            return False, "Image file does not exist"
        
        # Check file size
        file_size = os.path.getsize(image_path)
        if file_size > 16 * 1024 * 1024:  # 16MB
            return False, "Image file too large"
        
        # Try to load image
        image = cv2.imread(image_path)
        if image is None:
            return False, "Could not load image"
        
        # Check image dimensions
        height, width = image.shape[:2]
        if height < 100 or width < 100:
            return False, "Image too small"
        
        # Check for face in image
        import face_recognition
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_image)
        
        if len(face_locations) == 0:
            return False, "No face detected in image"
        elif len(face_locations) > 1:
            return False, "Multiple faces detected in image"
        
        return True, "Image is valid"
        
    except Exception as e:
        logger.error(f"Error validating image: {str(e)}")
        return False, f"Error validating image: {str(e)}"

def resize_image(image, max_width=800, max_height=600):
    """Resize image while maintaining aspect ratio"""
    try:
        height, width = image.shape[:2]
        
        # Calculate scaling factor
        scale_x = max_width / width
        scale_y = max_height / height
        scale = min(scale_x, scale_y, 1.0)  # Don't upscale
        
        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            return resized_image
        
        return image
        
    except Exception as e:
        logger.error(f"Error resizing image: {str(e)}")
        return image

def enhance_image_quality(image):
    """Enhance image quality for better face recognition"""
    try:
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        
        # Convert back to BGR
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Apply bilateral filter for noise reduction
        filtered = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        return filtered
        
    except Exception as e:
        logger.error(f"Error enhancing image quality: {str(e)}")
        return image

def save_image(image, path):
    """Save image to specified path"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save image
        cv2.imwrite(path, image)
        return True
        
    except Exception as e:
        logger.error(f"Error saving image: {str(e)}")
        return False

def draw_face_box(image, face_location, name, confidence):
    """Draw bounding box around face with name and confidence"""
    try:
        top, right, bottom, left = face_location
        
        # Draw rectangle
        cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
        
        # Draw label background
        cv2.rectangle(image, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
        
        # Draw text
        font = cv2.FONT_HERSHEY_DUPLEX
        text = f"{name} ({confidence:.2f})"
        cv2.putText(image, text, (left + 6, bottom - 6), font, 0.6, (0, 0, 0), 1)
        
        return image
        
    except Exception as e:
        logger.error(f"Error drawing face box: {str(e)}")
        return image

def crop_face(image, face_location, padding=20):
    """Crop face from image with padding"""
    try:
        top, right, bottom, left = face_location
        
        # Add padding
        height, width = image.shape[:2]
        top = max(0, top - padding)
        left = max(0, left - padding)
        bottom = min(height, bottom + padding)
        right = min(width, right + padding)
        
        # Crop image
        cropped = image[top:bottom, left:right]
        
        return cropped
        
    except Exception as e:
        logger.error(f"Error cropping face: {str(e)}")
        return image
