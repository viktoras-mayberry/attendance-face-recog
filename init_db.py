#!/usr/bin/env python3
"""
Database initialization script for the Face Recognition Attendance System.
This script creates the database tables and sets up the initial configuration.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask
from config.config import config
from database.models import db, User, FaceEncoding, AttendanceRecord, SystemLog

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config['development'])
    db.init_app(app)
    return app

def init_database():
    """Initialize the database with tables."""
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✓ Database tables created successfully!")
            
            # Create necessary directories
            directories = [
                'static/uploads',
                'data/faces',
                'data/training',
                'data/unknown',
                'logs',
                'models'
            ]
            
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
            
            print("✓ Required directories created!")
            
            # Check if tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            expected_tables = ['users', 'face_encodings', 'attendance_records', 'system_logs']
            
            for table in expected_tables:
                if table in tables:
                    print(f"✓ Table '{table}' exists")
                else:
                    print(f"✗ Table '{table}' missing")
            
            print("\n🎉 Database initialization completed successfully!")
            print("You can now run the application with: python src/app.py")
            
        except Exception as e:
            print(f"❌ Error initializing database: {str(e)}")
            return False
    
    return True

if __name__ == '__main__':
    init_database()
