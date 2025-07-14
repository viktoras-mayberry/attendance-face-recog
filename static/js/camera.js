// Camera functionality for attendance capture
let video;
let canvas;
let context;

document.addEventListener('DOMContentLoaded', function() {
    video = document.getElementById('camera');
    canvas = document.getElementById('canvas');
    context = canvas.getContext('2d');
    
    // Initialize camera
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(stream) {
                video.srcObject = stream;
                video.play();
            })
            .catch(function(error) {
                console.error('Error accessing camera: ', error);
                alert('Error accessing camera. Please check permissions.');
            });
    }
    
    // Capture button event
    document.getElementById('capture-btn').addEventListener('click', function() {
        captureImage();
    });
});

function captureImage() {
    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw video frame to canvas
    context.drawImage(video, 0, 0);
    
    // Convert canvas to blob and send to server
    canvas.toBlob(function(blob) {
        let formData = new FormData();
        formData.append('image', blob, 'capture.jpg');
        
        fetch('/capture', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Attendance captured successfully!');
            } else {
                alert('Error capturing attendance: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error capturing attendance.');
        });
    });
}
