import face_recognition
import cv2
import numpy as np
import os
import logging
from config.config import Config
from database.models import FaceEncoding

logger = logging.getLogger(__name__)

class FaceRecognition:
    """Class to handle face recognition tasks"""
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_ids = []

    def load_known_faces(self):
        """Load known face encodings from the database"""
        try:
            known_faces = FaceEncoding.query.all()
            for face in known_faces:
                self.known_face_encodings.append(np.array(json.loads(face.encoding_data)))
                self.known_face_ids.append(face.user_id)
            logger.info(f"Loaded {len(self.known_face_encodings)} known faces from database.")
        except Exception as e:
            logger.error(f"Error loading known faces: {str(e)}")

    def recognize_faces_in_image(self, image):
        """Recognize faces in a given image and return matches"""
        # Convert from BGR to RGB
        rgb_image = image[:, :, ::-1]
        
        # Find all face locations and their encodings
        face_locations = face_recognition.face_locations(rgb_image, model=Config.FACE_RECOGNITION_MODEL)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        matches = []

        for face_encoding, face_location in zip(face_encodings, face_locations):
            distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_idx = np.argmin(distances)
            if distances[best_match_idx] < Config.FACE_RECOGNITION_TOLERANCE:
                matches.append((self.known_face_ids[best_match_idx], face_location, distances[best_match_idx]))

        return matches

    def mark_attendance(self, face_id):
        """Record attendance for a given face ID"""
        # This method should interact with the database to mark attendance for the user
        logger.info(f"Marking attendance for user ID {face_id}")
        # Not implemented yet
        pass

    def add_new_face(self, image, user_id):
        """Add a new face encoding to the database"""
        # Convert from BGR to RGB
        rgb_image = image[:, :, ::-1]
        
        # Find face locations and encodings
        face_locations = face_recognition.face_locations(rgb_image, model=Config.FACE_RECOGNITION_MODEL)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

        if len(face_encodings) == 1:
            # Save the encoding to the database
            encoding = face_encodings[0]
            new_face = FaceEncoding(user_id=user_id)
            new_face.set_encoding_array(encoding)
            db.session.add(new_face)
            db.session.commit()
            logger.info(f"Added new face for user ID {user_id}")
        else:
            logger.warning(f"Failed to add face for user ID {user_id}. Number of faces found: {len(face_encodings)}")
