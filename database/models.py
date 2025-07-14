from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    """User model for storing employee information"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    position = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    face_encodings = db.relationship('FaceEncoding', backref='user', lazy=True, cascade='all, delete-orphan')
    attendance_records = db.relationship('AttendanceRecord', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.name} ({self.employee_id})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'name': self.name,
            'email': self.email,
            'department': self.department,
            'position': self.position,
            'phone': self.phone,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class FaceEncoding(db.Model):
    """Face encoding model for storing face recognition data"""
    __tablename__ = 'face_encodings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    encoding_data = db.Column(db.Text, nullable=False)  # JSON string of face encoding
    image_path = db.Column(db.String(255), nullable=False)
    quality_score = db.Column(db.Float, default=0.0)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<FaceEncoding {self.id} for User {self.user_id}>'
    
    def get_encoding_array(self):
        """Convert JSON string back to numpy array"""
        import numpy as np
        return np.array(json.loads(self.encoding_data))
    
    def set_encoding_array(self, encoding_array):
        """Convert numpy array to JSON string"""
        import numpy as np
        self.encoding_data = json.dumps(encoding_array.tolist())

class AttendanceRecord(db.Model):
    """Attendance record model"""
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False)  # 'IN', 'OUT'
    confidence = db.Column(db.Float, default=0.0)  # Recognition confidence
    image_path = db.Column(db.String(255))  # Path to captured image
    location = db.Column(db.String(100))  # Optional location info
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<AttendanceRecord {self.user_id} - {self.status} at {self.timestamp}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'employee_id': self.user.employee_id if self.user else None,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
            'confidence': self.confidence,
            'image_path': self.image_path,
            'location': self.location,
            'notes': self.notes
        }

class SystemLog(db.Model):
    """System log model for tracking system events"""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    level = db.Column(db.String(20), nullable=False)  # INFO, WARNING, ERROR
    message = db.Column(db.Text, nullable=False)
    module = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    def __repr__(self):
        return f'<SystemLog {self.level}: {self.message[:50]}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'message': self.message,
            'module': self.module,
            'user_id': self.user_id
        }
