"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql://postgres:drowssap@localhost:5432/warbler_test"


# Now we can import app

from app import app

app.config['TESTING'] = True

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

class UserModelTestCase(TestCase):
    """Test model for Users."""

    def setUp(self):
        """Create test client, add sample data."""
        self.client = app.test_client()
        self.context = app.app_context()
        self.context.push()
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        self.user1 = User(
                email="test1@test.com",
                username="testuser1",
                password="HASHED_PASSWORD"
            )
        self.user2 = User(
                email="test2@test.com",
                username="testuser2",
                password="HASHED_PASSWORD"
            )
        
        db.session.add(self.user1)
        db.session.add(self.user2)
        db.session.commit()

    def tearDown(self):
        
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        db.session.commit()
        self.context.pop()
        

    def test_user_model(self):
        """Does basic model work?"""
        
        self.assertEqual(len(self.user1.messages), 0)
        self.assertEqual(len(self.user1.followers), 0)
        self.assertIn("<User #", str(self.user1))

    def test_user_follow(self):
        """"Testing following and follower functionality"""
        
        u1 = self.user1
        u2 = self.user2
        u1.following.append(u2)
            
        self.assertTrue(u2.is_followed_by(u1))
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u2.followers[0].id, u1.id)

        self.assertFalse(u1.is_followed_by(u2))
        self.assertFalse(u2.is_following(u1))

    def test_user_create(self):
        """Testing creation of users"""
        
        u = User.signup(username = 'signup_test',email = 'signup@test.com', password = 'password', image_url='k')
        db.session.commit()
        self.assertEqual(u, User.query.get(u.id))
        user = User.signup(None,email = 'asdc@test.com', password = 'password', image_url='k')
        self.assertIs(type(user),Exception)

    def test_user_authenticate(self):
        """Testing user authentication"""
        
        user = User.signup(username = 'authuser', email = 'signup@test.com', password = 'password')
        db.session.commit()
        validUser = User.authenticate(user.username, 'password')
        invalidName = User.authenticate("doesnotexist", 'password')
        invalidPassword = User.authenticate(user.username, "isnotcorrect")
        self.assertEqual(user.username,validUser.username)
        self.assertFalse(invalidName)
        self.assertFalse(invalidPassword)