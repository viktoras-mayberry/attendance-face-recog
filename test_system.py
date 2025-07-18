#!/usr/bin/env python3
"""
Comprehensive testing script for the Face Recognition Attendance System
This script tests all major functionalities
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
TEST_IMAGE_PATH = "test_image.jpg"

def create_test_image():
    """Create a simple test image for upload"""
    try:
        import cv2
        import numpy as np
        
        # Create a simple test image (100x100 pixels)
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:] = (100, 150, 200)  # Light blue background
        
        # Add some text
        cv2.putText(img, 'TEST', (25, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Save the image
        cv2.imwrite(TEST_IMAGE_PATH, img)
        print(f"✅ Created test image: {TEST_IMAGE_PATH}")
        return True
    except Exception as e:
        print(f"❌ Error creating test image: {e}")
        return False

def test_server_connection():
    """Test if server is running and accessible"""
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and accessible")
            return True
        else:
            print(f"❌ Server responded with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def test_home_page():
    """Test the home page loads correctly"""
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            if "Face Recognition Attendance System" in response.text:
                print("✅ Home page loads correctly")
                return True
            else:
                print("❌ Home page content not as expected")
                return False
        else:
            print(f"❌ Home page failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing home page: {e}")
        return False

def test_employee_registration():
    """Test employee registration functionality"""
    try:
        # Create test image if not exists
        if not os.path.exists(TEST_IMAGE_PATH):
            create_test_image()
        
        # Prepare registration data
        data = {
            'name': 'John Doe Test',
            'email': f'john.doe.test.{int(time.time())}@example.com',
            'department': 'IT Testing',
            'position': 'Test Engineer',
            'phone': '+1234567890'
        }
        
        # Prepare file for upload
        with open(TEST_IMAGE_PATH, 'rb') as f:
            files = {'file': ('test_image.jpg', f, 'image/jpeg')}
            
            response = requests.post(f"{BASE_URL}/register", data=data, files=files)
            
            if response.status_code == 302:  # Redirect after successful registration
                print("✅ Employee registration successful")
                return True
            else:
                print(f"❌ Registration failed with status: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error testing employee registration: {e}")
        return False

def test_admin_dashboard():
    """Test admin dashboard functionality"""
    try:
        response = requests.get(f"{BASE_URL}/admin")
        if response.status_code == 200:
            if "Admin Dashboard" in response.text:
                print("✅ Admin dashboard loads correctly")
                return True
            else:
                print("❌ Admin dashboard content not as expected")
                return False
        else:
            print(f"❌ Admin dashboard failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing admin dashboard: {e}")
        return False

def test_attendance_page():
    """Test attendance capture page"""
    try:
        response = requests.get(f"{BASE_URL}/attendance")
        if response.status_code == 200:
            if "Attendance Capture" in response.text:
                print("✅ Attendance page loads correctly")
                return True
            else:
                print("❌ Attendance page content not as expected")
                return False
        else:
            print(f"❌ Attendance page failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing attendance page: {e}")
        return False

def test_attendance_capture():
    """Test attendance capture functionality"""
    try:
        response = requests.post(f"{BASE_URL}/capture")
        if response.status_code == 302:  # Redirect after capture
            print("✅ Attendance capture functionality works")
            return True
        else:
            print(f"❌ Attendance capture failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing attendance capture: {e}")
        return False

def test_css_and_static_files():
    """Test if CSS and static files are loading"""
    try:
        css_response = requests.get(f"{BASE_URL}/static/css/style.css")
        if css_response.status_code == 200:
            print("✅ CSS file loads correctly")
            return True
        else:
            print(f"❌ CSS file failed with status: {css_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing CSS file: {e}")
        return False

def run_all_tests():
    """Run all tests and provide summary"""
    print("🚀 Starting comprehensive testing of Face Recognition Attendance System")
    print("=" * 80)
    
    tests = [
        ("Server Connection", test_server_connection),
        ("Home Page", test_home_page),
        ("CSS & Static Files", test_css_and_static_files),
        ("Employee Registration", test_employee_registration),
        ("Admin Dashboard", test_admin_dashboard),
        ("Attendance Page", test_attendance_page),
        ("Attendance Capture", test_attendance_capture),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        print("-" * 40)
        result = test_func()
        results.append((test_name, result))
        time.sleep(1)  # Small delay between tests
    
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 Overall Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! The system is working perfectly!")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    # Cleanup
    if os.path.exists(TEST_IMAGE_PATH):
        os.remove(TEST_IMAGE_PATH)
        print(f"🧹 Cleaned up test image: {TEST_IMAGE_PATH}")
    
    return failed == 0

if __name__ == "__main__":
    run_all_tests()
