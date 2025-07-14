import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    DEBUG = False
    TESTING = False
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///attendance.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload configuration
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Face recognition configuration
    FACE_RECOGNITION_TOLERANCE = 0.6  # Lower is more strict
    FACE_RECOGNITION_MODEL = 'hog'  # 'hog' or 'cnn'
    
    # Data paths
    FACES_DATA_PATH = 'data/faces'
    TRAINING_DATA_PATH = 'data/training'
    UNKNOWN_DATA_PATH = 'data/unknown'
    MODELS_PATH = 'models'
    
    # Logging configuration
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/attendance.log'
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Camera configuration
    CAMERA_INDEX = 0
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    
    # Attendance configuration
    ATTENDANCE_BUFFER_TIME = 300  # 5 minutes buffer to prevent duplicate entries
    
    # Email configuration (optional)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FACE_RECOGNITION_MODEL = 'hog'  # Faster for development

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FACE_RECOGNITION_MODEL = 'cnn'  # More accurate for production
    FACE_RECOGNITION_TOLERANCE = 0.5

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
