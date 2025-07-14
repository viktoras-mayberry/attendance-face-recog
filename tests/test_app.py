import unittest
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import app
from database.models import db, User

class TestApp(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """Clean up after each test method."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        """Test the home page route."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_user_creation(self):
        """Test user creation."""
        user = User(
            employee_id='EMP0001',
            name='John Doe',
            email='john@example.com',
            department='IT',
            position='Developer'
        )
        db.session.add(user)
        db.session.commit()
        
        retrieved_user = User.query.filter_by(email='john@example.com').first()
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.name, 'John Doe')

if __name__ == '__main__':
    unittest.main()
