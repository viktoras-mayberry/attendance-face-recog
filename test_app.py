#!/usr/bin/env python3
"""
Simple test script to run the Face Recognition Attendance System
"""

import os
import sys
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import cv2
import numpy as np
from werkzeug.utils import secure_filename
import logging

# Mock face recognition for testing
class MockFaceRecognition:
    def __init__(self):
        self.known_faces = []
        self.known_names = []
        self.known_ids = []
    
    def add_face(self, user_id, name, image_path):
        # Mock adding a face
        self.known_faces.append(np.random.random(128))
        self.known_names.append(name)
        self.known_ids.append(user_id)
        return True
    
    def recognize_face(self, image):
        # Mock face recognition - return first known face if any
        if self.known_faces:
            return {
                'user_id': self.known_ids[0],
                'name': self.known_names[0],
                'confidence': 0.85
            }
        return None

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Initialize database
db = SQLAlchemy(app)

# Initialize mock face recognition
face_recognition_service = MockFaceRecognition()

# Simple User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    position = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_clearance_status(self):
        return {
            'current_attendance': 3,
            'required_attendance': 5,
            'clearance_granted': False,
            'clearance_level': 'LOW'
        }

# Simple AttendanceRecord model
class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='IN')
    confidence = db.Column(db.Float, default=0.0)

# Routes
@app.route('/')
def home():
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    today_attendance = AttendanceRecord.query.filter(
        db.func.date(AttendanceRecord.timestamp) == datetime.now().date()
    ).count()
    
    return render_template('index.html', 
                         total_users=total_users,
                         active_users=active_users,
                         today_attendance=today_attendance)

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    department = request.form.get('department')
    position = request.form.get('position')
    phone = request.form.get('phone')
    file = request.files.get('file')
    
    if not name or not email or not department or not file:
        flash('Please fill in all required fields')
        return redirect(url_for('home'))
    
    # Check if user exists
    if User.query.filter_by(email=email).first():
        flash('User with this email already exists')
        return redirect(url_for('home'))
    
    # Create user
    employee_id = f"EMP{User.query.count() + 1:04d}"
    user = User(
        employee_id=employee_id,
        name=name,
        email=email,
        department=department,
        position=position,
        phone=phone
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Save uploaded file
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        
        # Add to face recognition
        face_recognition_service.add_face(user.id, name, filepath)
    
    flash(f'User {name} registered successfully with ID: {employee_id}')
    return redirect(url_for('home'))

@app.route('/capture', methods=['POST'])
def capture():
    # Mock attendance capture
    if face_recognition_service.known_faces:
        # Create attendance record
        attendance = AttendanceRecord(
            user_id=face_recognition_service.known_ids[0],
            status='IN',
            confidence=0.85
        )
        db.session.add(attendance)
        db.session.commit()
        
        flash(f'Attendance marked for {face_recognition_service.known_names[0]}')
    else:
        flash('No registered users found')
    
    return redirect(url_for('home'))

@app.route('/attendance')
def attendance():
    return render_template('attendance.html')

@app.route('/admin')
def admin():
    users = User.query.all()
    report = []
    for user in users:
        clearance_status = user.get_clearance_status()
        report.append({
            'employee_id': user.employee_id,
            'name': user.name,
            'department': user.department,
            'clearance_level': clearance_status['clearance_level'],
            'current_attendance': clearance_status['current_attendance'],
            'required_attendance': clearance_status['required_attendance'],
            'clearance_granted': clearance_status['clearance_granted']
        })
    
    return render_template('admin.html', report=report)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")
    
    print("🚀 Starting Face Recognition Attendance System...")
    print("📱 Access the application at: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop the server")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {str(e)}")
