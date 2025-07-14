#!/usr/bin/env python3
"""
Simple run script for the Face Recognition Attendance System.
This script starts the Flask application with proper configuration.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import app

if __name__ == '__main__':
    # Set environment variables if needed
    os.environ.setdefault('FLASK_ENV', 'development')
    
    print("🚀 Starting Face Recognition Attendance System...")
    print("📱 Access the application at: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop the server")
    
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {str(e)}")
