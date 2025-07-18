#!/usr/bin/env python3
"""
Mock face recognition module for testing when face_recognition is not available.
This provides the same interface as the real face_recognition library but with dummy data.
"""

import numpy as np
import cv2
import random

def face_locations(image, number_of_times_to_upsample=1, model="hog"):
    """
    Mock face locations detection.
    Returns dummy face locations for testing.
    """
    height, width = image.shape[:2]
    
    # Mock detection - return a face in the center area
    if random.random() > 0.3:  # 70% chance of detecting a face
        center_x = width // 2
        center_y = height // 2
        face_width = min(width, height) // 4
        face_height = face_width
        
        top = max(0, center_y - face_height // 2)
        bottom = min(height, center_y + face_height // 2)
        left = max(0, center_x - face_width // 2)
        right = min(width, center_x + face_width // 2)
        
        return [(top, right, bottom, left)]
    else:
        return []

def face_encodings(image, known_face_locations=None, num_jitters=1, model="small"):
    """
    Mock face encodings generation.
    Returns dummy 128-dimensional face encodings.
    """
    if known_face_locations is None:
        known_face_locations = face_locations(image)
    
    encodings = []
    for location in known_face_locations:
        # Generate a random 128-dimensional encoding
        encoding = np.random.random(128)
        encodings.append(encoding)
    
    return encodings

def compare_faces(known_face_encodings, face_encoding_to_check, tolerance=0.6):
    """
    Mock face comparison.
    Returns random matches for testing.
    """
    if len(known_face_encodings) == 0:
        return []
    
    matches = []
    for known_encoding in known_face_encodings:
        # Random match with 60% probability
        match = random.random() < 0.6
        matches.append(match)
    
    return matches

def face_distance(face_encodings, face_to_compare):
    """
    Mock face distance calculation.
    Returns random distances for testing.
    """
    if len(face_encodings) == 0:
        return np.array([])
    
    distances = []
    for encoding in face_encodings:
        # Generate random distance between 0 and 1
        distance = random.random()
        distances.append(distance)
    
    return np.array(distances)

def load_image_file(file_path):
    """
    Mock image loading.
    Uses OpenCV to load the image.
    """
    image = cv2.imread(file_path)
    if image is not None:
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return image

# For compatibility with real face_recognition library
def api_face_locations(image, number_of_times_to_upsample=1, model="hog"):
    return face_locations(image, number_of_times_to_upsample, model)

def api_face_encodings(image, known_face_locations=None, num_jitters=1, model="small"):
    return face_encodings(image, known_face_locations, num_jitters, model)

def api_compare_faces(known_face_encodings, face_encoding_to_check, tolerance=0.6):
    return compare_faces(known_face_encodings, face_encoding_to_check, tolerance)

def api_face_distance(face_encodings, face_to_compare):
    return face_distance(face_encodings, face_to_compare)

print("Mock face recognition module loaded - for testing purposes only")
