from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import config, Config
from face_recognition_service import FaceRecognitionService
from database.models import db, User, FaceEncoding, AttendanceRecord
from utils.image_utils import validate_face_image
from werkzeug.utils import secure_filename
import cv2
import logging
from sqlalchemy.exc import SQLAlchemyError

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config['development'])

# Initialize database
db = SQLAlchemy(app)

# Initialize face recognition service
face_recognition_service = FaceRecognitionService()

# Set up logging
logging.basicConfig(filename=Config.LOG_FILE, level=logging.INFO)

@app.route('/', methods=['GET'])
def home():
    """Home page."""
    return render_template('index.html')

@app.route('/capture', methods=['GET', 'POST'])
def capture():
    """Capture attendance with the camera."""
    if request.method == 'POST':
        cap = None
        try:
            cap = cv2.VideoCapture(Config.CAMERA_INDEX)
            if not cap.isOpened():
                flash('Failed to access camera. Please check if camera is connected.')
                return redirect(url_for('home'))

            ret, frame = cap.read()
            if not ret:
                flash('Failed to capture image from camera')
                return redirect(url_for('home'))

            results = face_recognition_service.recognize_faces_in_frame(frame)
            
            recognized_users = []
            for result in results:
                user_id = result['user_id']
                if user_id:
                    success = face_recognition_service.mark_attendance(
                        user_id, 
                        confidence=result['confidence'],
                        image_path=None
                    )
                    if success:
                        recognized_users.append(result['name'])

            if recognized_users:
                flash(f'Attendance marked for: {", ".join(recognized_users)}')
            else:
                flash('No recognized faces found. Please try again.')

        except Exception as e:
            logging.error(f"Error capturing attendance: {str(e)}")
            flash('Error occurred while capturing attendance. Please try again.')
        finally:
            if cap:
                cap.release()
        
    return redirect(url_for('home'))

@app.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    file = request.files.get('file')
    name = request.form.get('name')
    email = request.form.get('email')
    department = request.form.get('department')
    position = request.form.get('position')
    phone = request.form.get('phone')

    if not file or not name or not email:
        flash('Please provide all required fields and a valid image.')
        return redirect(url_for('home'))

    try:
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('User with this email already exists.')
            return redirect(url_for('home'))

        # Create upload folder if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

        # Save file
        filename = secure_filename(file.filename)
        if not filename:
            flash('Invalid file name.')
            return redirect(url_for('home'))

        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Validate image
        valid, message = validate_face_image(filepath)
        if not valid:
            # Remove the saved file if validation fails
            if os.path.exists(filepath):
                os.remove(filepath)
            flash(message)
            return redirect(url_for('home'))

        # Generate employee ID
        employee_id = f"EMP{User.query.count() + 1:04d}"

        # Add user to database
        new_user = User(
            employee_id=employee_id,
            name=name,
            email=email,
            department=department,
            position=position,
            phone=phone
        )
        db.session.add(new_user)
        db.session.commit()

        # Add face encoding
        success = face_recognition_service.add_user_face(new_user.id, filepath)
        if not success:
            # Rollback user creation if face encoding fails
            db.session.delete(new_user)
            db.session.commit()
            if os.path.exists(filepath):
                os.remove(filepath)
            flash('Failed to process face image. Please try again.')
            return redirect(url_for('home'))

        flash(f'User registered successfully! Employee ID: {employee_id}')
        return redirect(url_for('home'))

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error registering user: {str(e)}")
        flash('Database error occurred. Please try again.')
        return redirect(url_for('home'))
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error registering user: {str(e)}")
        flash(f"Error: {str(e)}")
        return redirect(url_for('home'))

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    """Capture attendance via webcam."""
    if request.method == 'POST':
        # This would be implemented with actual webcam integration.
        flash('Attendance captured successfully!')
        return redirect(url_for('home'))
    else:
        return render_template('attendance.html')

if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all()
    except SQLAlchemyError as e:
        logging.error(f"Error initializing the database: {str(e)}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
