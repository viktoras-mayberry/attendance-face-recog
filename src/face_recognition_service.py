import face_recognition
import cv2
import numpy as np
import os
import json
import logging
from datetime import datetime, timedelta
from PIL import Image
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import db, User, FaceEncoding, AttendanceRecord, SystemLog
from config.config import Config
from utils.image_utils import preprocess_image, validate_face_image

logger = logging.getLogger(__name__)

class FaceRecognitionService:
    """Comprehensive face recognition service"""
    
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.tolerance = Config.FACE_RECOGNITION_TOLERANCE
        self.model = Config.FACE_RECOGNITION_MODEL
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load all known face encodings from database"""
        try:
            self.known_face_encodings = []
            self.known_face_names = []
            self.known_face_ids = []
            
            face_encodings = FaceEncoding.query.join(User).filter(User.is_active == True).all()
            
            for face_encoding in face_encodings:
                try:
                    encoding_array = face_encoding.get_encoding_array()
                    self.known_face_encodings.append(encoding_array)
                    self.known_face_names.append(face_encoding.user.name)
                    self.known_face_ids.append(face_encoding.user_id)
                except Exception as e:
                    logger.error(f"Error loading face encoding {face_encoding.id}: {str(e)}")
            
            logger.info(f"Loaded {len(self.known_face_encodings)} known faces from database")
            
            # Log to system
            self._log_system_event("INFO", f"Loaded {len(self.known_face_encodings)} face encodings", "FaceRecognitionService")
            
        except Exception as e:
            logger.error(f"Error loading known faces: {str(e)}")
            self._log_system_event("ERROR", f"Error loading known faces: {str(e)}", "FaceRecognitionService")
    
    def recognize_faces_in_frame(self, frame):
        """Recognize faces in a video frame"""
        try:
            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = small_frame[:, :, ::-1]
            
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(rgb_small_frame, model=self.model)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            results = []
            
            for face_encoding, face_location in zip(face_encodings, face_locations):
                # Scale back up face locations
                top, right, bottom, left = face_location
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                
                # Check if face matches any known face
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=self.tolerance)
                distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                
                user_id = None
                name = "Unknown"
                confidence = 0.0
                
                if len(distances) > 0:
                    best_match_index = np.argmin(distances)
                    if matches[best_match_index]:
                        user_id = self.known_face_ids[best_match_index]
                        name = self.known_face_names[best_match_index]
                        confidence = 1.0 - distances[best_match_index]
                
                results.append({
                    'user_id': user_id,
                    'name': name,
                    'confidence': confidence,
                    'location': (top, right, bottom, left)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error recognizing faces: {str(e)}")
            return []
    
    def add_user_face(self, user_id, image_path):
        """Add a new face encoding for a user"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError(f"User with ID {user_id} not found")
            
            # Load and validate image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image from {image_path}")
            
            # Preprocess image
            processed_image = preprocess_image(image)
            
            # Convert to RGB
            rgb_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
            
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(rgb_image, model=self.model)
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            if len(face_encodings) == 0:
                raise ValueError("No face found in the image")
            elif len(face_encodings) > 1:
                raise ValueError("Multiple faces found in the image")
            
            # Calculate quality score
            quality_score = self._calculate_face_quality(face_locations[0], rgb_image)
            
            # Create new face encoding record
            face_encoding = FaceEncoding(
                user_id=user_id,
                image_path=image_path,
                quality_score=quality_score
            )
            face_encoding.set_encoding_array(face_encodings[0])
            
            # Set as primary if it's the first encoding for this user
            existing_encodings = FaceEncoding.query.filter_by(user_id=user_id).count()
            if existing_encodings == 0:
                face_encoding.is_primary = True
            
            db.session.add(face_encoding)
            db.session.commit()
            
            # Reload known faces
            self.load_known_faces()
            
            logger.info(f"Added face encoding for user {user.name} (ID: {user_id})")
            self._log_system_event("INFO", f"Added face encoding for user {user.name}", "FaceRecognitionService", user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding face for user {user_id}: {str(e)}")
            self._log_system_event("ERROR", f"Error adding face for user {user_id}: {str(e)}", "FaceRecognitionService", user_id)
            return False
    
    def mark_attendance(self, user_id, status='IN', confidence=0.0, image_path=None):
        """Mark attendance for a user"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError(f"User with ID {user_id} not found")
            
            # Check for duplicate attendance within buffer time
            buffer_time = datetime.now() - timedelta(seconds=Config.ATTENDANCE_BUFFER_TIME)
            recent_record = AttendanceRecord.query.filter_by(user_id=user_id)\
                                                 .filter(AttendanceRecord.timestamp >= buffer_time)\
                                                 .first()
            
            if recent_record:
                logger.warning(f"Duplicate attendance attempt for user {user.name} within buffer time")
                return False
            
            # Create attendance record
            attendance = AttendanceRecord(
                user_id=user_id,
                status=status,
                confidence=confidence,
                image_path=image_path
            )
            
            db.session.add(attendance)
            db.session.commit()
            
            logger.info(f"Marked attendance for {user.name} - Status: {status}, Confidence: {confidence:.2f}")
            self._log_system_event("INFO", f"Attendance marked for {user.name} - {status}", "FaceRecognitionService", user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking attendance for user {user_id}: {str(e)}")
            self._log_system_event("ERROR", f"Error marking attendance: {str(e)}", "FaceRecognitionService", user_id)
            return False
    
    def get_attendance_today(self, user_id=None):
        """Get today's attendance records"""
        try:
            today = datetime.now().date()
            query = AttendanceRecord.query.filter(
                db.func.date(AttendanceRecord.timestamp) == today
            )
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            return query.order_by(AttendanceRecord.timestamp.desc()).all()
            
        except Exception as e:
            logger.error(f"Error getting today's attendance: {str(e)}")
            return []
    
    def get_user_attendance_status(self, user_id):
        """Get current attendance status for a user"""
        try:
            today = datetime.now().date()
            records = AttendanceRecord.query.filter_by(user_id=user_id)\
                                          .filter(db.func.date(AttendanceRecord.timestamp) == today)\
                                          .order_by(AttendanceRecord.timestamp.desc())\
                                          .all()
            
            if not records:
                return "NOT_MARKED"
            
            return records[0].status
            
        except Exception as e:
            logger.error(f"Error getting user attendance status: {str(e)}")
            return "ERROR"
    
    def _calculate_face_quality(self, face_location, image):
        """Calculate quality score for a face"""
        try:
            top, right, bottom, left = face_location
            face_image = image[top:bottom, left:right]
            
            # Calculate various quality metrics
            height, width = face_image.shape[:2]
            area = height * width
            
            # Size score (larger faces are generally better)
            size_score = min(area / 10000, 1.0)
            
            # Sharpness score using Laplacian variance
            gray = cv2.cvtColor(face_image, cv2.COLOR_RGB2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(sharpness / 1000, 1.0)
            
            # Combine scores
            quality_score = (size_score + sharpness_score) / 2
            
            return quality_score
            
        except Exception as e:
            logger.error(f"Error calculating face quality: {str(e)}")
            return 0.0
    
    def _log_system_event(self, level, message, module, user_id=None):
        """Log system event to database"""
        try:
            log_entry = SystemLog(
                level=level,
                message=message,
                module=module,
                user_id=user_id
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging system event: {str(e)}")
    
    def train_model(self):
        """Train/retrain the face recognition model"""
        try:
            self.load_known_faces()
            self._log_system_event("INFO", "Face recognition model retrained", "FaceRecognitionService")
            return True
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            self._log_system_event("ERROR", f"Error training model: {str(e)}", "FaceRecognitionService")
            return False
