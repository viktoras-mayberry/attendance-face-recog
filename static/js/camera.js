// Face Recognition Attendance System - Camera Interface
// This script handles camera access, location tracking, and face recognition

class AttendanceCamera {
    constructor() {
        this.video = document.getElementById('camera');
        this.canvas = document.getElementById('canvas');
        this.captureBtn = document.getElementById('capture-btn');
        this.locationStatus = document.getElementById('location-status');
        this.faceStatus = document.getElementById('face-status');
        
        this.stream = null;
        this.userLocation = null;
        this.isLocationValid = false;
        this.faceDetected = false;
        
        this.init();
    }
    
    async init() {
        try {
            // Get user location first
            await this.getUserLocation();
            
            // Start camera
            await this.startCamera();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Start face detection
            this.startFaceDetection();
            
        } catch (error) {
            console.error('Initialization error:', error);
            this.showError('Failed to initialize camera system');
        }
    }
    
    async getUserLocation() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                this.locationStatus.textContent = 'Location not supported';
                this.locationStatus.className = 'error';
                reject(new Error('Geolocation not supported'));
                return;
            }
            
            this.locationStatus.textContent = 'Getting location...';
            
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.userLocation = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude
                    };
                    
                    // Validate location with server
                    this.validateLocation();
                    resolve(this.userLocation);
                },
                (error) => {
                    console.error('Location error:', error);
                    this.locationStatus.textContent = 'Location access denied';
                    this.locationStatus.className = 'error';
                    reject(error);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 60000
                }
            );
        });
    }
    
    async validateLocation() {
        if (!this.userLocation) {
            this.isLocationValid = false;
            this.locationStatus.textContent = 'Location not available';
            this.locationStatus.className = 'error';
            return;
        }
        
        try {
            const response = await fetch('/api/validate-location', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.userLocation)
            });
            
            const result = await response.json();
            
            if (result.valid) {
                this.isLocationValid = true;
                this.locationStatus.textContent = `Location valid: ${result.office_name}`;
                this.locationStatus.className = 'success';
            } else {
                this.isLocationValid = false;
                this.locationStatus.textContent = 'Not in office location';
                this.locationStatus.className = 'error';
            }
        } catch (error) {
            console.error('Location validation error:', error);
            this.isLocationValid = false;
            this.locationStatus.textContent = 'Location validation failed';
            this.locationStatus.className = 'error';
        }
        
        this.updateCaptureButton();
    }
    
    async startCamera() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                }
            });
            
            this.video.srcObject = this.stream;
            
            // Wait for video to load
            await new Promise((resolve) => {
                this.video.onloadedmetadata = resolve;
            });
            
            console.log('Camera started successfully');
            
        } catch (error) {
            console.error('Camera error:', error);
            this.showError('Failed to access camera');
        }
    }
    
    setupEventListeners() {
        this.captureBtn.addEventListener('click', () => this.captureAttendance());
        
        // Handle page unload
        window.addEventListener('beforeunload', () => {
            this.stopCamera();
        });
    }
    
    startFaceDetection() {
        // Simple face detection using video analysis
        // In a real implementation, you'd use a face detection library
        setInterval(() => {
            if (this.video.videoWidth > 0 && this.video.videoHeight > 0) {
                // Mock face detection - in reality, use face-api.js or similar
                this.faceDetected = true;
                this.faceStatus.textContent = 'Face detected - Ready to capture';
                this.faceStatus.className = 'success';
            } else {
                this.faceDetected = false;
                this.faceStatus.textContent = 'No face detected';
                this.faceStatus.className = 'warning';
            }
            
            this.updateCaptureButton();
        }, 1000);
    }
    
    updateCaptureButton() {
        const canCapture = this.isLocationValid && this.faceDetected;
        this.captureBtn.disabled = !canCapture;
        
        if (canCapture) {
            this.captureBtn.textContent = 'Capture Attendance';
            this.captureBtn.className = 'btn-primary';
        } else {
            this.captureBtn.textContent = 'Waiting for location and face...';
            this.captureBtn.className = 'btn-disabled';
        }
    }
    
    async captureAttendance() {
        if (!this.isLocationValid || !this.faceDetected) {
            this.showError('Cannot capture - location or face not validated');
            return;
        }
        
        try {
            // Capture frame from video
            const canvas = this.canvas;
            const ctx = canvas.getContext('2d');
            
            canvas.width = this.video.videoWidth;
            canvas.height = this.video.videoHeight;
            
            ctx.drawImage(this.video, 0, 0);
            
            // Convert to blob
            const blob = await new Promise(resolve => {
                canvas.toBlob(resolve, 'image/jpeg', 0.8);
            });
            
            // Send to server
            const formData = new FormData();
            formData.append('image', blob, 'attendance.jpg');
            formData.append('latitude', this.userLocation.latitude);
            formData.append('longitude', this.userLocation.longitude);
            
            this.captureBtn.disabled = true;
            this.captureBtn.textContent = 'Processing...';
            
            const response = await fetch('/api/capture-attendance', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess(`Attendance captured for ${result.user_name}`);
                
                // Redirect after a short delay
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
            } else {
                this.showError(result.message || 'Failed to capture attendance');
            }
            
        } catch (error) {
            console.error('Capture error:', error);
            this.showError('Error capturing attendance');
        } finally {
            this.captureBtn.disabled = false;
            this.updateCaptureButton();
        }
    }
    
    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }
    
    showError(message) {
        // Create or update error message
        let errorDiv = document.getElementById('error-message');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'error-message';
            errorDiv.className = 'error-message';
            document.body.insertBefore(errorDiv, document.body.firstChild);
        }
        
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }
    
    showSuccess(message) {
        // Create or update success message
        let successDiv = document.getElementById('success-message');
        if (!successDiv) {
            successDiv = document.createElement('div');
            successDiv.id = 'success-message';
            successDiv.className = 'success-message';
            document.body.insertBefore(successDiv, document.body.firstChild);
        }
        
        successDiv.textContent = message;
        successDiv.style.display = 'block';
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            successDiv.style.display = 'none';
        }, 3000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AttendanceCamera();
});

// Fallback for older browsers
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new AttendanceCamera();
    });
} else {
    new AttendanceCamera();
}
