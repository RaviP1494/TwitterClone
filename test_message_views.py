"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User
from flask import session


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql://postgres:drowssap@localhost:5432/warbler_test"


# Now we can import app

from app import app, CURR_USER_KEY

app.config['TESTING'] = True

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
with app.app_context():
    db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        self.context = app.app_context()
        self.context.push()
        self.client = app.test_client()
        db.drop_all()
        db.create_all()

        User.query.delete()
        Message.query.delete()
        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 9999
        self.testuser.id = self.testuser_id
        db.session.commit()

    def tearDown(self):
        self.context.pop()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            unauthorized_response = c.post("messages/new", data={"text": "ouch"})
            self.assertEqual(unauthorized_response.status_code, 302)
            self.assertIn(b'<a href="/"',unauthorized_response.data)

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            
            resp = c.post("/messages/new", data={"text": "Hello"})
        
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_show_message(self):
        with self.client as c:

            msg = Message(text = "boop", user_id = self.testuser.id)
            db.session.add(msg)
            db.session.commit()
            show_msg_resp = c.get(f"messages/{msg.id}")
            self.assertIn(b'boop',show_msg_resp.data)
            self.assertEqual(show_msg_resp.status_code, 200)

    def test_destroy_message(self):
        with self.client as c:
            
            msg = Message(text = "boop", user_id = self.testuser.id)
            db.session.add(msg)
            db.session.commit()

            unauthorized_response = c.post(f"/messages/{msg.id}/delete")
            self.assertEqual(unauthorized_response.status_code, 302)
            self.assertIn(b'<a href="/"',unauthorized_response.data)

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            authorized_response = c.post(f"/messages/{msg.id}/delete")
            self.assertEqual(len(self.testuser.messages), 0)
            self.assertEqual(authorized_response.status_code, 302)