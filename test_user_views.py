"""User View Tests"""

import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from flask import session

os.environ['DATABASE_URL'] = "postgresql://postgres:drowssap@localhost:5432/warbler_test"

from app import app, CURR_USER_KEY

app.config['TESTING'] = True

with app.app_context():
    db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for users."""

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

    def test_user_signup(self):
        with self.client as c:
            signup_get_response = c.get("/signup")
            self.assertEqual(signup_get_response.status_code, 200)
            self.assertIn(b'Join Warbler today.',signup_get_response.data)

            bad_signup_post_response = c.post("/signup", data={"username":"test_user1"})
            self.assertEqual(bad_signup_post_response.status_code, 200)
            self.assertIn(b'Join Warbler today.',bad_signup_post_response.data)
            self.assertEqual(len(User.query.all()),1)

            signup_post_response = c.post("/signup", data={"username":"test_user2", "email": "test_user@email.com", "password":"password"})
            self.assertEqual(signup_post_response.status_code, 302)
            self.assertIn(b'<a href="/"',signup_post_response.data)

            user = User.query.filter_by(username="test_user2").one()
            self.assertEqual(user.username, "test_user2")

    def test_user_login(self):
        with self.client as c:
            login_get_response = c.get("/login")
            self.assertEqual(login_get_response.status_code, 200)
            self.assertIn(b"Log in", login_get_response.data)

            bad_login_response = c.post("/login", data={"username":"baduser","password":"badpass"})
            self.assertEqual(login_get_response.status_code, 200)
            self.assertIn(b"Log in", login_get_response.data)

            login_response = c.post("/login", data={"username":"testuser", "password":"testuser"})
            with c.session_transaction() as sess:
                self.assertEqual(sess[CURR_USER_KEY], 9999)
            self.assertEqual(login_response.status_code, 302)
            self.assertIn(b'<a href="/"',login_response.data)

    def test_user_logout(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 9999
            
            logout_response = c.get("/logout")
            self.assertIn(b"/login",logout_response.data)
            self.assertEqual(logout_response.status_code, 302)

            with c.session_transaction() as sess:
                self.assertFalse(CURR_USER_KEY in sess)

    def test_list_users(self):
        with self.client as c:
            resp = c.get("/users")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"testuser", resp.data)

    def test_users_show(self):
        with self.client as c:
            resp = c.get(f"users/{self.testuser.id}")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"testuser", resp.data)

    def test_show_follow(self):
        with self.client as c:
            following_resp = c.get(f"/users/{self.testuser.id}/following")
            self.assertEqual(following_resp.status_code, 302)
            self.assertIn(b'<a href="/"',following_resp.data)

            followers_resp = c.get(f"/users/{self.testuser.id}/followers")
            self.assertEqual(followers_resp.status_code, 302)
            self.assertIn(b'<a href="/"',followers_resp.data)

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            following_resp = c.get(f"/users/{self.testuser.id}/following")
            self.assertEqual(following_resp.status_code, 200)
            
            followers_resp = c.get(f"/users/{self.testuser.id}/followers")
            self.assertEqual(followers_resp.status_code, 200)

    def test_add_follow(self):
        with self.client as c:
            followed_user = User.signup("testuser2","test@user.com","password")
            db.session.commit()
            follow_resp = c.post(f"/users/follow/{followed_user.id}")
            self.assertEqual(follow_resp.status_code, 302)
            self.assertIn(b'<a href="/"',follow_resp.data)
            self.assertEqual(len(self.testuser.following),0)

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            follow_resp = c.post(f"/users/follow/{followed_user.id}")
            self.assertEqual(follow_resp.status_code, 302)
            self.assertIn(b'<a href="/users/',follow_resp.data)
            self.assertEqual(len(self.testuser.following),1)

    def test_stop_follow(self):
        with self.client as c:
            followed_user = User.signup("testuser2","test@user.com","password")
            self.testuser.following.append(followed_user)
            db.session.commit()

            stop_follow_resp = c.post(f"/users/stop-following/{followed_user.id}")
            self.assertEqual(len(self.testuser.following), 1)
            self.assertIn(b'<a href="/"', stop_follow_resp.data)
            self.assertEqual(stop_follow_resp.status_code, 302)

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            stop_follow_resp = c.post(f"/users/stop-following/{followed_user.id}")
            self.assertEqual(len(self.testuser.following),0)
            self.assertEqual(stop_follow_resp.status_code, 302)
            self.assertIn(b'<a href="/users/',stop_follow_resp.data)

    def test_delete_user(self):
        with self.client as c:
            delete_user_resp = c.post("/users/delete")
            self.assertEqual(delete_user_resp.status_code, 302)
            self.assertIn(b'<a href="/"', delete_user_resp.data)
            self.assertEqual(User.query.get_or_404(self.testuser.id),self.testuser)

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            delete_user_resp = c.post("/users/delete")
            self.assertEqual(delete_user_resp.status_code, 302)
            self.assertIn(b'<a href="/signup', delete_user_resp.data)
            self.assertEqual(len(User.query.all()),0)

    def test_edit_user(self):
        with self.client as c:
            edit_form_data = {"username":"testuser", "password":"testuser", "email":"edited@email.com", "bio":"wow", "image_url":"https://i.redd.it/z97fbpd64s9a1.jpg", "header_image_url":"https://i.redd.it/z97fbpd64s9a1.jpg"}

            edit_get_resp = c.get("/users/profile")
            self.assertEqual(edit_get_resp.status_code, 302)
            self.assertIn(b'<a href="/"', edit_get_resp.data)

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            edit_get_resp = c.get("/users/profile")
            self.assertEqual(edit_get_resp.status_code, 200)
            self.assertIn(b'Edit this user!', edit_get_resp.data)
            
            edit_post_resp = c.post("/users/profile", data=edit_form_data)
            self.assertEqual(edit_post_resp.status_code, 302)
            self.assertIn(b'<a href="/users/',edit_post_resp.data)
            self.assertEqual(self.testuser.email, edit_form_data["email"])
