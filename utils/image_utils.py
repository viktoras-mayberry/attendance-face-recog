#!/usr/bin/env python3
"""
Image processing utilities for the Face Recognition Attendance System.
This module handles image preprocessing, validation, and quality assessment.
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance
import logging
from config.config import Config

# Try to import face_recognition, fallback to mock if not available
try:
    import face_recognition
    print("Using real face_recognition library")
except ImportError:
    print("face_recognition not available, using mock version")
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import mock_face_recognition as face_recognition

logger = logging.getLogger(__name__)

def validate_face_image(image_path):
    """
    Validate if the image contains a clear, single face suitable for recognition.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        tuple: (is_valid, message) - Boolean indicating validity and descriptive message
    """
    try:
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            return False, "Could not load image file"
        
        # Convert to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Check image dimensions
        height, width = rgb_image.shape[:2]
        if width < 100 or height < 100:
            return False, "Image too small. Minimum size is 100x100 pixels"
        
        if width > 4000 or height > 4000:
            return False, "Image too large. Maximum size is 4000x4000 pixels"
        
        # Check for faces
        face_locations = face_recognition.face_locations(rgb_image)
        
        if len(face_locations) == 0:
            return False, "No face detected in the image"
        
        if len(face_locations) > 1:
            return False, "Multiple faces detected. Please use an image with only one face"
        
        # Check face size relative to image
        face_location = face_locations[0]
        top, right, bottom, left = face_location
        face_width = right - left
        face_height = bottom - top
        
        # Face should be at least 20% of image width/height
        if face_width < width * 0.2 or face_height < height * 0.2:
            return False, "Face too small in the image. Please use a closer photo"
        
        # Check image quality
        quality_score = assess_image_quality(rgb_image, face_location)
        if quality_score < 0.5:
            return False, f"Image quality too low (score: {quality_score:.2f}). Please use a clearer image"
        
        # Check if face encoding can be generated
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        if len(face_encodings) == 0:
            return False, "Could not generate face encoding from the image"
        
        return True, "Image is valid for face recognition"
        
    except Exception as e:
        logger.error(f"Error validating image {image_path}: {str(e)}")
        return False, f"Error processing image: {str(e)}"

def preprocess_image(image):
    """
    Preprocess image for better face recognition results.
    
    Args:
        image (numpy.ndarray): Input image
        
    Returns:
        numpy.ndarray: Preprocessed image
    """
    try:
        # Convert to PIL Image for easier processing
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(1.2)
        
        # Enhance brightness slightly
        enhancer = ImageEnhance.Brightness(pil_image)
        pil_image = enhancer.enhance(1.1)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(pil_image)
        pil_image = enhancer.enhance(1.1)
        
        # Convert back to OpenCV format
        processed_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        # Apply noise reduction
        processed_image = cv2.bilateralFilter(processed_image, 9, 75, 75)
        
        return processed_image
        
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        return image  # Return original image if preprocessing fails

def assess_image_quality(image, face_location):
    """
    Assess the quality of a face image for recognition purposes.
    
    Args:
        image (numpy.ndarray): RGB image
        face_location (tuple): Face location coordinates (top, right, bottom, left)
        
    Returns:
        float: Quality score between 0 and 1
    """
    try:
        top, right, bottom, left = face_location
        
        # Extract face region
        face_image = image[top:bottom, left:right]
        
        # Convert to grayscale for analysis
        gray_face = cv2.cvtColor(face_image, cv2.COLOR_RGB2GRAY)
        
        # Calculate sharpness (Laplacian variance)
        laplacian_var = cv2.Laplacian(gray_face, cv2.CV_64F).var()
        sharpness_score = min(laplacian_var / 1000, 1.0)  # Normalize to 0-1
        
        # Calculate brightness
        brightness = np.mean(gray_face) / 255.0
        brightness_score = 1.0 - abs(brightness - 0.5) * 2  # Penalize too dark or too bright
        
        # Calculate contrast
        contrast = np.std(gray_face) / 255.0
        contrast_score = min(contrast * 4, 1.0)  # Normalize to 0-1
        
        # Calculate overall quality score
        quality_score = (sharpness_score * 0.4 + brightness_score * 0.3 + contrast_score * 0.3)
        
        return quality_score
        
    except Exception as e:
        logger.error(f"Error assessing image quality: {str(e)}")
        return 0.5  # Return neutral score if assessment fails

def resize_image(image, max_width=800, max_height=600):
    """
    Resize image while maintaining aspect ratio.
    
    Args:
        image (numpy.ndarray): Input image
        max_width (int): Maximum width
        max_height (int): Maximum height
        
    Returns:
        numpy.ndarray: Resized image
    """
    try:
        height, width = image.shape[:2]
        
        # Calculate scaling factor
        scale_width = max_width / width
        scale_height = max_height / height
        scale = min(scale_width, scale_height, 1.0)  # Don't upscale
        
        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            return resized_image
        
        return image
        
    except Exception as e:
        logger.error(f"Error resizing image: {str(e)}")
        return image

def detect_and_crop_face(image_path, output_path=None, padding=20):
    """
    Detect face in image and crop to face region with padding.
    
    Args:
        image_path (str): Path to input image
        output_path (str): Path to save cropped image (optional)
        padding (int): Padding around face in pixels
        
    Returns:
        numpy.ndarray or None: Cropped face image, or None if no face found
    """
    try:
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            return None
        
        # Convert to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Find face locations
        face_locations = face_recognition.face_locations(rgb_image)
        
        if len(face_locations) == 0:
            return None
        
        # Use the first face found
        top, right, bottom, left = face_locations[0]
        
        # Add padding
        height, width = rgb_image.shape[:2]
        top = max(0, top - padding)
        bottom = min(height, bottom + padding)
        left = max(0, left - padding)
        right = min(width, right + padding)
        
        # Crop face
        face_image = rgb_image[top:bottom, left:right]
        
        # Convert back to BGR for saving
        face_bgr = cv2.cvtColor(face_image, cv2.COLOR_RGB2BGR)
        
        # Save if output path provided
        if output_path:
            cv2.imwrite(output_path, face_bgr)
        
        return face_bgr
        
    except Exception as e:
        logger.error(f"Error cropping face from {image_path}: {str(e)}")
        return None

def normalize_lighting(image):
    """
    Normalize lighting conditions in an image.
    
    Args:
        image (numpy.ndarray): Input image
        
    Returns:
        numpy.ndarray: Image with normalized lighting
    """
    try:
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Split the LAB image into L, A, and B channels
        l_channel, a_channel, b_channel = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_channel = clahe.apply(l_channel)
        
        # Merge channels and convert back to BGR
        lab = cv2.merge([l_channel, a_channel, b_channel])
        normalized_image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return normalized_image
        
    except Exception as e:
        logger.error(f"Error normalizing lighting: {str(e)}")
        return image

def save_processed_image(image, output_path, quality=95):
    """
    Save processed image with specified quality.
    
    Args:
        image (numpy.ndarray): Image to save
        output_path (str): Output file path
        quality (int): JPEG quality (0-100)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Set compression parameters
        if output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
            params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        elif output_path.lower().endswith('.png'):
            params = [cv2.IMWRITE_PNG_COMPRESSION, 9]
        else:
            params = []
        
        # Save image
        success = cv2.imwrite(output_path, image, params)
        
        if success:
            logger.info(f"Image saved successfully to {output_path}")
        else:
            logger.error(f"Failed to save image to {output_path}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error saving image to {output_path}: {str(e)}")
        return False
