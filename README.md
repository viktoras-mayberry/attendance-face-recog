# Face Recognition Attendance System

A comprehensive Flask-based web application for managing student and employee attendance using advanced face recognition technology, location validation, and administrative controls.

## 🚀 Key Features

### Core Functionality
- **Multi-User System**: Supports both students and employees with different registration flows
- **Advanced Face Recognition**: Automatic face detection and recognition with confidence scoring
- **Location-Based Attendance**: GPS-based location validation for attendance marking
- **Real-time Camera Integration**: Capture attendance using webcam or mobile camera
- **Quality Validation**: Comprehensive face image quality assessment during registration
- **Duplicate Prevention**: Intelligent duplicate attendance prevention with buffer time

### Administrative Features
- **Multi-Level Admin System**: Super admin and view-only admin roles
- **Student Management**: Complete student registration and profile management
- **Attendance Analytics**: Weekly attendance tracking and analytics
- **Location Management**: Define and manage valid attendance locations
- **Clearance System**: Attendance-based clearance level management
- **Notification System**: Email and SMS notifications for attendance reports
- **Data Export**: CSV export functionality for attendance records

### Security & Validation
- **Secure Authentication**: Password hashing and session management
- **Role-Based Access Control**: Different access levels for students and admins
- **Image Quality Assessment**: Automatic face image quality scoring
- **Location Validation**: GPS-based attendance location verification

## Technology Stack

- **Backend**: Flask, SQLAlchemy, Python
- **Face Recognition**: face_recognition library, OpenCV, dlib
- **Database**: SQLite (configurable to other databases)
- **Image Processing**: PIL, OpenCV, NumPy
- **Frontend**: HTML, CSS, JavaScript

## Project Structure

```
ATTENDANCE_FACE_RECOGNITION_SYSTEM/
├── config/
│   └── config.py              # Configuration settings
├── database/
│   └── models.py              # Database models
├── src/
│   ├── app.py                 # Main Flask application
│   └── face_recognition_service.py  # Face recognition service
├── utils/
│   ├── face_recognition.py    # Face recognition utilities
│   └── image_utils.py         # Image processing utilities
├── templates/
│   ├── index.html             # Home page template
│   └── attendance.html        # Attendance capture page
├── static/
│   ├── css/
│   │   └── style.css          # Stylesheet
│   ├── js/
│   │   └── camera.js          # Camera functionality
│   ├── images/                # Static images
│   └── uploads/               # Uploaded user images
├── data/
│   ├── faces/                 # Face data storage
│   ├── training/              # Training data
│   └── unknown/               # Unknown faces
├── logs/                      # Application logs
├── models/                    # Trained models
├── tests/                     # Test files
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```

## Installation

### Prerequisites

- Python 3.7+
- Webcam/Camera for attendance capture
- Git

### Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/ATTENDANCE_FACE_RECOGNITION_SYSTEM.git
   cd ATTENDANCE_FACE_RECOGNITION_SYSTEM
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (optional):
   Create a `.env` file in the root directory:
   ```
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///attendance.db
   ```

5. **Run the application**:
   ```bash
   cd src
   python app.py
   ```

6. **Access the application**:
   Open your browser and go to `http://localhost:5000`

## Usage

### Employee Registration

1. Navigate to the home page
2. Fill in the registration form with employee details
3. Upload a clear face image
4. Click "Register" to add the employee

### Attendance Capture

1. Click "Capture Attendance" on the home page
2. The system will access your camera
3. Position your face in front of the camera
4. The system will automatically recognize and mark attendance

## Configuration

### Database Configuration

Edit `config/config.py` to modify database settings:

```python
# SQLite (default)
SQLALCHEMY_DATABASE_URI = 'sqlite:///attendance.db'

# PostgreSQL
SQLALCHEMY_DATABASE_URI = 'postgresql://username:password@localhost/attendance'

# MySQL
SQLALCHEMY_DATABASE_URI = 'mysql://username:password@localhost/attendance'
```

### Face Recognition Settings

Adjust face recognition parameters in `config/config.py`:

```python
FACE_RECOGNITION_TOLERANCE = 0.6  # Lower = more strict
FACE_RECOGNITION_MODEL = 'hog'    # 'hog' or 'cnn'
```

### Camera Settings

Configure camera parameters:

```python
CAMERA_INDEX = 0        # Camera device index
CAMERA_WIDTH = 640      # Camera width
CAMERA_HEIGHT = 480     # Camera height
```

## 🔌 API Endpoints

### Authentication
- `GET /login` - Login page
- `POST /login` - Process login (student/admin)
- `GET /logout` - Logout user

### Student Routes
- `GET /register` - Student registration page
- `POST /register` - Process student registration
- `GET /profile` - Student profile page
- `POST /profile` - Update student profile
- `GET /attendance` - Attendance capture page
- `POST /attendance` - Process attendance marking
- `GET /profile/export_csv` - Export student attendance CSV

### Admin Routes
- `GET /admin` - Admin dashboard
- `GET /admin/create` - Create new admin (super admin only)
- `POST /admin/create` - Process admin creation
- `GET /admin/locations` - Manage office locations
- `POST /admin/locations` - Add/remove office locations
- `POST /admin/send_weekly_report` - Send weekly email reports
- `POST /admin/send_weekly_sms` - Send weekly SMS reports
- `GET /admin/export_csv` - Export admin attendance CSV

### System Routes
- `GET /` - Home page (requires login)
- `POST /capture` - Camera-based attendance capture
- `POST /register_employee` - Register new employee

## 🗄️ Database Models

### User Model
- `id`: Primary key
- `student_id`: Unique student identifier
- `name`: Student/Employee name
- `email`: Email address
- `state_code`: State code (for students)
- `ppa`: PPA information (for students)
- `cds_group`: CDS group (for students)
- `phone`: Phone number
- `password_hash`: Hashed password
- `is_active`: Active status
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Admin Model
- `id`: Primary key
- `name`: Admin name
- `email`: Email address
- `phone`: Phone number
- `password_hash`: Hashed password
- `role`: Admin role (super_admin/view_only)
- `is_active`: Active status

### FaceEncoding Model
- `id`: Primary key
- `user_id`: Foreign key to User
- `encoding_data`: Face encoding data (JSON)
- `image_path`: Path to face image
- `quality_score`: Face image quality score
- `is_primary`: Primary encoding flag

### AttendanceRecord Model
- `id`: Primary key
- `user_id`: Foreign key to User
- `timestamp`: Attendance timestamp
- `status`: Attendance status (IN/OUT/BREAK/LUNCH)
- `confidence`: Recognition confidence score
- `location_latitude`: GPS latitude
- `location_longitude`: GPS longitude
- `location_name`: Location name
- `is_valid_location`: Location validation flag

### OfficeLocation Model
- `id`: Primary key
- `name`: Location name
- `address`: Physical address
- `latitude`: GPS latitude
- `longitude`: GPS longitude
- `radius`: Valid radius in meters
- `is_active`: Active status
- `required_clearance_level`: Required clearance level

### ClearanceRecord Model
- `id`: Primary key
- `user_id`: Foreign key to User
- `week_start`: Week start date
- `week_end`: Week end date
- `attendance_count`: Weekly attendance count
- `required_count`: Required attendance count
- `clearance_granted`: Clearance status
- `clearance_level`: Clearance level

### SystemLog Model
- `id`: Primary key
- `timestamp`: Log timestamp
- `level`: Log level (INFO/WARNING/ERROR)
- `message`: Log message
- `module`: Source module
- `user_id`: Associated user ID

### NotificationLog Model
- `id`: Primary key
- `user_id`: Target user ID
- `type`: Notification type (email/sms)
- `recipient`: Recipient address
- `message`: Notification message
- `status`: Delivery status

## Troubleshooting

### Common Issues

1. **Camera not working**:
   - Check camera permissions
   - Ensure no other applications are using the camera
   - Try different camera index values

2. **Face not recognized**:
   - Ensure good lighting conditions
   - Use a clear, front-facing image during registration
   - Adjust face recognition tolerance

3. **Database errors**:
   - Check database connection settings
   - Ensure database file permissions are correct

4. **Installation issues**:
   - Install Visual Studio C++ Build Tools (Windows)
   - Install cmake and dlib dependencies
   - Use Python 3.7-3.9 for better compatibility

### Performance Tips

- Use 'hog' model for faster processing
- Reduce image resolution for better performance
- Use 'cnn' model for better accuracy (requires more resources)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please create an issue in the GitHub repository.

## Acknowledgments

- face_recognition library by Adam Geitgey
- OpenCV community
- Flask framework developers
