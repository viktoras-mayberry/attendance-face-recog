from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json
from enum import Enum

db = SQLAlchemy()

class AttendanceStatus(Enum):
    IN = 'IN'
    OUT = 'OUT'
    BREAK = 'BREAK'
    LUNCH = 'LUNCH'

class ClearanceLevel(Enum):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    RESTRICTED = 'RESTRICTED'

class User(db.Model):
    """User model for storing student information"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    state_code = db.Column(db.String(20), nullable=False)
    ppa = db.Column(db.String(100), nullable=False)
    cds_group = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    face_encodings = db.relationship('FaceEncoding', backref='user', lazy=True, cascade='all, delete-orphan')
    attendance_records = db.relationship('AttendanceRecord', backref='user', lazy=True)
    clearance_records = db.relationship('ClearanceRecord', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.name} ({self.student_id})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'email': self.email,
            'state_code': self.state_code,
            'ppa': self.ppa,
            'cds_group': self.cds_group,
            'phone': self.phone,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def get_weekly_attendance_count(self, week_start=None):
        """Get attendance count for the current week"""
        if week_start is None:
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
        
        week_end = week_start + timedelta(days=6)
        
        return AttendanceRecord.query.filter(
            AttendanceRecord.user_id == self.id,
            AttendanceRecord.timestamp >= week_start,
            AttendanceRecord.timestamp <= week_end,
            AttendanceRecord.status == AttendanceStatus.IN.value
        ).count()
    
    def get_clearance_status(self):
        """Get current clearance status based on weekly attendance"""
        weekly_count = self.get_weekly_attendance_count()
        return {
            'current_attendance': weekly_count,
            'required_attendance': self.required_weekly_attendance,
            'clearance_granted': weekly_count >= self.required_weekly_attendance,
            'clearance_level': self.clearance_level.value if self.clearance_level else None
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
    status = db.Column(db.Enum(AttendanceStatus), nullable=False, default=AttendanceStatus.IN)
    confidence = db.Column(db.Float, default=0.0)  # Recognition confidence
    image_path = db.Column(db.String(255))  # Path to captured image
    location_latitude = db.Column(db.Float)  # GPS latitude
    location_longitude = db.Column(db.Float)  # GPS longitude
    location_name = db.Column(db.String(100))  # Human-readable location
    ip_address = db.Column(db.String(45))  # IP address for logging
    user_agent = db.Column(db.String(255))  # Browser/device info
    is_valid_location = db.Column(db.Boolean, default=False)  # Location validation
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
            'status': self.status.value if self.status else None,
            'confidence': self.confidence,
            'image_path': self.image_path,
            'location_latitude': self.location_latitude,
            'location_longitude': self.location_longitude,
            'location_name': self.location_name,
            'ip_address': self.ip_address,
            'is_valid_location': self.is_valid_location,
            'notes': self.notes
        }

class OfficeLocation(db.Model):
    """Office location model for defining valid attendance locations"""
    __tablename__ = 'office_locations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    radius = db.Column(db.Float, default=100.0)  # Radius in meters
    is_active = db.Column(db.Boolean, default=True)
    required_clearance_level = db.Column(db.Enum(ClearanceLevel), default=ClearanceLevel.LOW)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<OfficeLocation {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'radius': self.radius,
            'is_active': self.is_active,
            'required_clearance_level': self.required_clearance_level.value if self.required_clearance_level else None,
            'created_at': self.created_at.isoformat()
        }
    
    def is_within_range(self, latitude, longitude):
        """Check if given coordinates are within the office location radius"""
        from math import radians, cos, sin, asin, sqrt
        
        # Haversine formula to calculate distance
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(latitude), radians(longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        distance = 6371000 * c  # Earth's radius in meters
        
        return distance <= self.radius

class ClearanceRecord(db.Model):
    """Clearance record model for tracking weekly clearance status"""
    __tablename__ = 'clearance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    week_start = db.Column(db.Date, nullable=False)
    week_end = db.Column(db.Date, nullable=False)
    attendance_count = db.Column(db.Integer, default=0)
    required_count = db.Column(db.Integer, default=5)
    clearance_granted = db.Column(db.Boolean, default=False)
    clearance_level = db.Column(db.Enum(ClearanceLevel), default=ClearanceLevel.LOW)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ClearanceRecord {self.user_id} - Week {self.week_start}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'employee_id': self.user.employee_id if self.user else None,
            'week_start': self.week_start.isoformat(),
            'week_end': self.week_end.isoformat(),
            'attendance_count': self.attendance_count,
            'required_count': self.required_count,
            'clearance_granted': self.clearance_granted,
            'clearance_level': self.clearance_level.value if self.clearance_level else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
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

# Admin model for admin users
class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'super_admin' or 'view_only'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Admin {self.name} ({self.role})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

# Notification log model for email/SMS logs
class NotificationLog(db.Model):
    __tablename__ = 'notification_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    type = db.Column(db.String(20), nullable=False)  # 'email' or 'sms'
    recipient = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(255))
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'sent', 'failed', etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<NotificationLog {self.type} to {self.recipient}>'
