from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import sys
import os
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func
import base64
from io import BytesIO
from PIL import Image
import csv
from flask import Response

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import config, Config
from face_recognition_service import FaceRecognitionService
from database.models import db, User, FaceEncoding, AttendanceRecord, OfficeLocation, ClearanceLevel
from utils.image_utils import validate_face_image
from utils.location_utils import is_user_in_office
from werkzeug.utils import secure_filename
import cv2
import logging
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
from database.models import Admin
from utils.face_recognition import recognize_face_for_user
from utils.location_utils import is_within_any_office_location
from utils.email_utils import init_mail, send_attendance_report_email
from utils.sms_utils import init_twilio, send_sms

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config['development'])
db.init_app(app)
init_mail(app)
init_twilio(app)

# Initialize face recognition service
face_recognition_service = FaceRecognitionService()

# Set up logging
logging.basicConfig(filename=Config.LOG_FILE, level=logging.INFO)

# Access control decorators

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session and 'admin_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'student':
            flash('Student access required.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Admin access required.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session or session.get('role') != 'super_admin':
            flash('Super admin access required.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Student profile route
@app.route('/profile', methods=['GET', 'POST'])
@student_required
def profile():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        phone = request.form.get('phone')
        cds_group = request.form.get('cds_group')
        if phone:
            user.phone = phone
        if cds_group:
            user.cds_group = cds_group
        db.session.commit()
        flash('Profile updated successfully.')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        if role == 'student':
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                session['role'] = 'student'
                flash('Login successful!')
                return redirect(url_for('home'))
            else:
                flash('Invalid student credentials.')
        elif role == 'admin':
            from database.models import Admin
            admin = Admin.query.filter_by(email=email).first()
            if admin and check_password_hash(admin.password_hash, password):
                session['admin_id'] = admin.id
                session['role'] = admin.role
                flash('Admin login successful!')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid admin credentials.')
        else:
            flash('Invalid role selected.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        state_code = request.form.get('state_code')
        ppa = request.form.get('ppa')
        cds_group = request.form.get('cds_group')
        password = request.form.get('password')
        image = request.files.get('image')
        if not all([name, email, phone, state_code, ppa, cds_group, password, image]):
            flash('Please fill in all fields.')
            return redirect(url_for('register'))
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('User with this email already exists.')
            return redirect(url_for('register'))
        # Save image
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        filename = secure_filename(image.filename)
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        image.save(filepath)
        # Hash password
        password_hash = generate_password_hash(password)
        # Generate student ID
        student_id = f"STU{User.query.count() + 1:04d}"
        new_user = User(
            student_id=student_id,
            name=name,
            email=email,
            phone=phone,
            state_code=state_code,
            ppa=ppa,
            cds_group=cds_group,
            password_hash=password_hash
        )
        db.session.add(new_user)
        db.session.commit()
        # Add face encoding (optional: implement face recognition logic here)
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

# Update home route to require login
@app.route('/', methods=['GET'])
def home():
    if 'user_id' not in session and 'admin_id' not in session:
        return redirect(url_for('login'))
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
                    user = User.query.get(user_id)
                    if not user:
                        continue

                    location_valid = is_user_in_office(request)
                    clearance_granted = user.get_clearance_status()['clearance_granted']

                    if not location_valid or not clearance_granted:
                        flash(f'{user.name} not authorized to mark attendance at this location or lacking clearance')
                        continue

                    success = face_recognition_service.mark_attendance(
                        user_id,
                        confidence=result['confidence'],
                        image_path=None,
                        location_valid=location_valid
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

@app.route('/register_employee', methods=['POST'])
def register_employee():
    """Register a new employee."""
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
@app.route('/admin', methods=['GET'])
@admin_required
def admin_dashboard():
    # Get all students
    students = User.query.order_by(User.name).all()
    # Weekly attendance per student
    attendance_data = []
    for student in students:
        weekly_attendance = student.get_weekly_attendance_count()
        attendance_data.append({
            'student': student,
            'weekly_attendance': weekly_attendance,
            'clearance_status': student.get_clearance_status()
        })
    # Analytics: students with low attendance
    low_attendance_students = [d for d in attendance_data if d['weekly_attendance'] < d['student'].get_clearance_status()['required_attendance']]
    # Total attendance this week
    total_attendance = sum([d['weekly_attendance'] for d in attendance_data])
    # Attendance trend (last 4 weeks)
    trends = []
    for i in range(4):
        week_start = (datetime.now().date() - timedelta(days=datetime.now().date().weekday())) - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        count = AttendanceRecord.query.filter(
            AttendanceRecord.timestamp >= week_start,
            AttendanceRecord.timestamp <= week_end,
            AttendanceRecord.status == 'IN'
        ).count()
        trends.append({'week': week_start.strftime('%Y-%m-%d'), 'count': count})
    # Role check
    is_super_admin = session.get('role') == 'super_admin'
    return render_template('admin.html',
        attendance_data=attendance_data,
        low_attendance_students=low_attendance_students,
        total_attendance=total_attendance,
        trends=trends[::-1],
        is_super_admin=is_super_admin
    )

@app.route('/admin/create', methods=['GET', 'POST'])
@super_admin_required
def admin_create():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        role = request.form.get('role')
        if not all([name, email, phone, password, role]):
            flash('Please fill in all fields.')
            return redirect(url_for('admin_create'))
        existing_admin = Admin.query.filter_by(email=email).first()
        if existing_admin:
            flash('Admin with this email already exists.')
            return redirect(url_for('admin_create'))
        password_hash = generate_password_hash(password)
        new_admin = Admin(
            name=name,
            email=email,
            phone=phone,
            password_hash=password_hash,
            role=role
        )
        db.session.add(new_admin)
        db.session.commit()
        flash('Admin account created successfully!')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_create.html')

@app.route('/admin/locations', methods=['GET', 'POST'])
@admin_required
def admin_locations():
    is_super_admin = session.get('role') == 'super_admin'
    if request.method == 'POST' and is_super_admin:
        # Remove location
        remove_id = request.form.get('remove_id')
        if remove_id:
            loc = OfficeLocation.query.get(int(remove_id))
            if loc:
                db.session.delete(loc)
                db.session.commit()
                flash('Location removed.')
            return redirect(url_for('admin_locations'))
        # Add location
        name = request.form.get('name')
        address = request.form.get('address')
        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)
        radius = request.form.get('radius', type=float)
        is_active = request.form.get('is_active') == '1'
        if all([name, address, latitude, longitude, radius]):
            new_loc = OfficeLocation(
                name=name,
                address=address,
                latitude=latitude,
                longitude=longitude,
                radius=radius,
                is_active=is_active
            )
            db.session.add(new_loc)
            db.session.commit()
            flash('Location added.')
            return redirect(url_for('admin_locations'))
        else:
            flash('Please fill in all fields for new location.')
    locations = OfficeLocation.query.order_by(OfficeLocation.name).all()
    return render_template('admin_locations.html', locations=locations, is_super_admin=is_super_admin)

@app.route('/attendance', methods=['GET', 'POST'])
@student_required
def attendance():
    if request.method == 'POST':
        image_data = request.form.get('image_data')
        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)
        if not image_data or latitude is None or longitude is None:
            flash('Missing image or location data.')
            return redirect(url_for('attendance'))
        # Decode image
        try:
            header, encoded = image_data.split(',', 1)
            img_bytes = base64.b64decode(encoded)
            img = Image.open(BytesIO(img_bytes))
        except Exception as e:
            flash('Invalid image data.')
            return redirect(url_for('attendance'))
        # Face recognition
        user = User.query.get(session['user_id'])
        recognized = recognize_face_for_user(user, img)
        if not recognized:
            flash('Face not recognized. Please try again.')
            return redirect(url_for('attendance'))
        # Location check
        location_valid, location_name = is_within_any_office_location(latitude, longitude)
        if not location_valid:
            flash('You are not at an allowed attendance location.')
            return redirect(url_for('attendance'))
        # Mark attendance
        record = AttendanceRecord(
            user_id=user.id,
            status='IN',
            confidence=1.0,
            image_path=None,  # Optionally save image to disk and store path
            location_latitude=latitude,
            location_longitude=longitude,
            location_name=location_name,
            is_valid_location=True
        )
        db.session.add(record)
        db.session.commit()
        flash('Attendance marked successfully!')
        return redirect(url_for('attendance'))
    return render_template('attendance.html')

@app.route('/admin/send_weekly_report', methods=['POST'])
@admin_required
def send_weekly_report():
    # For demonstration: send a simple weekly report to all students
    students = User.query.all()
    for student in students:
        report_text = f"Hello {student.name},\n\nHere is your weekly attendance summary.\nAttendance count: {student.get_weekly_attendance_count()}"
        send_attendance_report_email(student.email, report_text)
    flash('Weekly attendance report sent to all students.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/send_weekly_sms', methods=['POST'])
@super_admin_required
def send_weekly_sms():
    students = User.query.all()
    for student in students:
        if student.phone:
            sms_text = f"Hello {student.name}, your weekly attendance count: {student.get_weekly_attendance_count()}"
            try:
                send_sms(student.phone, sms_text)
            except Exception as e:
                print(f"Failed to send SMS to {student.phone}: {e}")
    flash('Weekly attendance SMS sent to all students with phone numbers.')
    return redirect(url_for('admin_dashboard'))

@app.route('/profile/export_csv')
@student_required
def export_student_attendance_csv():
    user = User.query.get(session['user_id'])
    # Get all attendance records for the current month
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    records = AttendanceRecord.query.filter(
        AttendanceRecord.user_id == user.id,
        AttendanceRecord.timestamp >= month_start
    ).order_by(AttendanceRecord.timestamp).all()
    def generate():
        yield 'Date,Status,Location\n'
        for r in records:
            yield f'{r.timestamp.date()},{r.status},{r.location_name or ""}\n'
    return Response(generate(), mimetype='text/csv', headers={
        'Content-Disposition': f'attachment; filename=attendance_{user.student_id}_{now.strftime("%Y_%m")}.csv'
    })

@app.route('/admin/export_csv')
@admin_required
def export_admin_attendance_csv():
    # Get all attendance records for the current week
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    records = AttendanceRecord.query.filter(
        AttendanceRecord.timestamp >= week_start,
        AttendanceRecord.timestamp <= week_end
    ).order_by(AttendanceRecord.timestamp).all()
    def generate():
        yield 'Student,Date,Status,Location\n'
        for r in records:
            yield f'{r.user.name},{r.timestamp.date()},{r.status},{r.location_name or ""}\n'
    return Response(generate(), mimetype='text/csv', headers={
        'Content-Disposition': f'attachment; filename=attendance_week_{week_start}.csv'
    })

if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all()
    except SQLAlchemyError as e:
        logging.error(f"Error initializing the database: {str(e)}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
