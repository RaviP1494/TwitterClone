"""Message Model tests"""

import os
from unittest import TestCase

from models import db, User, Message, Follows

os.environ['DATABASE_URL'] = "postgresql://postgres:drowssap@localhost:5432/warbler_test"

from app import app

app.config['TESTING'] = True

class MessageModelTestCase(TestCase):
    """Test model for Mesages."""

    def setUp(self):
        """Create test client, add sample data"""
        self.context = app.app_context()
        self.context.push()
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        self.user_pw = 'password'
        self.user = User.signup(username='tester', email='tester@test.com', password=self.user_pw)
        with app.test_client() as client:
            db.session.add(self.user)
            db.session.commit()

    def tearDown(self):
        """Remove app context"""
        self.context.pop()

    def test_message_model(self):
        message = Message(text='hello there', user_id = self.user.id)
        with app.test_client() as client:
            db.session.add(message)
            db.session.commit()
        self.assertEqual(len(self.user.messages),1)
        