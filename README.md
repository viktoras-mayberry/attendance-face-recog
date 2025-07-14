# Face Recognition Attendance System

A Flask-based web application for managing employee attendance using face recognition technology.

## Features

- **Employee Registration**: Register new employees with face images
- **Face Recognition**: Automatic face detection and recognition
- **Attendance Tracking**: Mark attendance with face recognition
- **Real-time Camera Integration**: Capture attendance using webcam
- **Database Management**: Store employee data and attendance records
- **Quality Validation**: Validate face image quality during registration
- **Duplicate Prevention**: Prevent duplicate attendance entries

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

## API Endpoints

- `GET /` - Home page
- `POST /register` - Register new employee
- `POST /capture` - Capture attendance
- `GET /attendance` - Attendance capture page

## Database Models

### User Model
- `id`: Primary key
- `employee_id`: Unique employee identifier
- `name`: Employee name
- `email`: Employee email
- `department`: Employee department
- `position`: Employee position
- `phone`: Employee phone number
- `is_active`: Employee status

### FaceEncoding Model
- `id`: Primary key
- `user_id`: Foreign key to User
- `encoding_data`: Face encoding data
- `image_path`: Path to face image
- `quality_score`: Face image quality score

### AttendanceRecord Model
- `id`: Primary key
- `user_id`: Foreign key to User
- `timestamp`: Attendance timestamp
- `status`: Attendance status ('IN'/'OUT')
- `confidence`: Recognition confidence score

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
