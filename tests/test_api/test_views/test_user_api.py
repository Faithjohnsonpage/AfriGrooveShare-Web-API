#!/usr/bin/env python3
import unittest
from io import BytesIO
from pathlib import Path
from PIL import Image
import os
import imghdr
from models.user import User
from models.news import News
from models import storage
from sqlalchemy.sql import text
from ..test_base_app import BaseTestCase
from unittest.mock import patch, Mock
from flask_caching import Cache
from flask import session, json
import io


MAX_IMAGE_LENGTH = 5 * 1000 * 1000
USER_PROFILE_UPLOAD = 'api/v1/uploads/profile_pics'


class TestAuthEndpoints(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        # Create a user instance
        cls.user = User()
        cls.user.username = "session_user"
        cls.user.email = "session@example.com"
        cls.user.password = "sessionpassword"

        storage.new(cls.user)
        storage.save()
        cls.test_user_id = cls.user.id

        # Create first news item
        cls.news1 = News()
        cls.news1.title = "Test News 1"
        cls.news1.content = "This is the first test news content."
        cls.news1.author = "John Doe"
        cls.news1.category = "Music Technology"
        cls.news1.user_id = cls.user.id
        storage.new(cls.news1)
        storage.save()
        cls.test_news1_id = cls.news1.id

        # Create second news item
        cls.news2 = News()
        cls.news2.title = "Test News 2"
        cls.news2.content = "This is the second test news content."
        cls.news2.author = "Jane Smith"
        cls.news2.category = "Music Trends"
        cls.news2.user_id = cls.user.id
        storage.new(cls.news2)
        storage.save()
        cls.test_news2_id = cls.news2.id

    @classmethod
    def tearDownClass(cls):
        """Teardown class-level resources"""

        # Delete news items first (due to foreign key constraints)
        news_to_delete = [cls.news1, cls.news2]
        for news in news_to_delete:
            if news and storage.get(News, news.id):
                storage.delete(news)
        storage.save()

        users_to_delete = [
            'test@example.com',
            'login@example.com',
            'session@example.com',
            'existing@example.com',
            'delete_user@example.com',
            'delete_another_user@example.com'
        ]
        for email in users_to_delete:
            user = storage.filter_by(User, email=email)
            if user:
                storage.delete(user)
        storage.save()

        # Clean up test files
        test_paths = [
            f"{cls.test_user_id}_profile.jpg",
            f"{cls.test_user_id}_profile_thumbnail.jpg"
        ]
        for filename in test_paths:
            path = os.path.join(USER_PROFILE_UPLOAD, filename)
            if os.path.exists(path):
                os.remove(path)

    def test_register(self):
        response = self.client.post('/auth/register', data={
            'username': 'new_user',
            'email': 'test@example.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn(b'User registered successfully', response.data)

    def test_register_missing_fields(self):
        response = self.client.post('/auth/register', data={
            'username': '',
            'email': 'test@example.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Missing fields', response.data)

    def test_register_email_already_registered(self):
        response = self.client.post('/auth/register', data={
            'username': 'another_user',
            'email': 'test@example.com',
            'password': 'password456'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Email already registered', response.data)

    def test_register_username_already_registered(self):
        response = self.client.post('/auth/register', data={
            'username': 'new_user',
            'email': 'newemail@example.com',
            'password': 'password456'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Username already exists', response.data)

    def test_register_invalid_username_length(self):
        """Test user registration with invalid username length"""
        # Test too short
        response = self.client.post('/auth/register', data={
            'username': 'ab',
            'email': 'newemail@example.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Username must be between 3 and 30 characters', response.data)

        # Test too long
        response = self.client.post('/auth/register', data={
            'username': 'a' * 31,
            'email': 'newemail@example.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Username must be between 3 and 30 characters', response.data)

    def test_login(self):
        # Register the user first
        self.client.post('/auth/register', data={
            'username': 'login_user',
            'email': 'login@example.com',
            'password': 'password456'
        })

        response = self.client.post('/auth/login', data={
            'email': 'login@example.com',
            'password': 'password456'
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged in successfully', response.data)

    def test_login_invalid_credentials(self):
        response = self.client.post('/auth/login', data={
            'email': 'invalid@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn(b'Invalid email or password', response.data)

    def login_user(self):
        """Helper method to log in the user and set up session"""
        with self.client.session_transaction() as session:
            session['user_id'] = self.test_user_id
            session['logged_in'] = True

    @patch('flask_caching.Cache.get')
    @patch('flask_caching.Cache.set')
    def test_get_profile(self, mock_cache_set, mock_cache_get):
        """Test profile retrieval with cache miss scenario"""
        # Configure cache mock to simulate cache miss
        mock_cache_get.return_value = None
        
        self.login_user()

        # Make the request
        response = self.client.get('/users/me')

        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'session_user', response.data)
        self.assertIn(b'session@example.com', response.data)

        # Verify cache interactions
        cache_key = f'user_profile:{self.test_user_id}'
        mock_cache_get.assert_called_once_with(cache_key)
        mock_cache_set.assert_called_once()

    @patch('flask_caching.Cache.get')
    def test_get_profile_cached(self, mock_cache_get):
        # Configure cache mock to simulate cache hit
        cached_profile = {
            'username': 'session_user',
            'email': 'session@example.com'
        }
        mock_cache_get.return_value = cached_profile
        
        # Log in the user
        self.login_user()
        
        # Make the request
        response = self.client.get('/users/me')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'session_user', response.data)
        self.assertIn(b'session@example.com', response.data)
        
        # Verify cache was checked
        cache_key = f'user_profile:{self.test_user_id}'
        mock_cache_get.assert_called_once_with(cache_key)

    def test_get_profile_unauthorized(self):
        """Test profile access without login"""
        response = self.client.get('/users/me')
        self.assertEqual(response.status_code, 401)
        self.assertIn(b'No active session', response.data)

    @patch('flask_caching.Cache.delete')
    @patch('api.v1.views.users.invalidate_all')
    def test_logout(self, mock_cache_invalidate, mock_cache_delete):
        """Test the user logout functionality"""
        # Log in the user
        self.login_user()

        # Log out the user
        response = self.client.post('/auth/logout')

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged out successfully', response.data)

        # Verify that the cache was cleared for the user's profile
        cache_key = f'user_profile:{self.test_user_id}'
        mock_cache_delete.assert_called_once_with(cache_key)

        # Verify that invalidate_all was called for all entities
        mock_cache_invalidate.assert_any_call('album')
        mock_cache_invalidate.assert_any_call('artist')
        mock_cache_invalidate.assert_any_call('music')
        mock_cache_invalidate.assert_any_call('playlist')
        mock_cache_invalidate.assert_any_call('news')

        # Ensure the session was cleared (if applicable, based on session logic)
        with self.client as client:
            with client.session_transaction() as sess:
                self.assertNotIn('user_id', sess)
                self.assertFalse(sess)

    @patch('flask_caching.Cache.delete')
    def test_update_profile(self, mock_cache_delete):
        """Test successful profile update"""
        self.login_user()

        response = self.client.put('/users/me', data={
            'username': 'updated_user'
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Profile updated successfully', response.data)

        cache_key = f'user_profile:{self.test_user_id}'
        mock_cache_delete.assert_called_once_with(cache_key)


    def test_update_profile_unauthorized(self):
        """Test profile update without login"""
        response = self.client.put('/users/me', data={
            'username': 'updated_user'
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn(b'Unauthorized', response.data)

    def test_update_profile_missing_username(self):
        """Test profile update with missing username"""
        self.login_user()
        response = self.client.put('/users/me', data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Valid username is required', response.data)

    def test_update_profile_invalid_username_length(self):
        """Test profile update with invalid username length"""
        self.login_user()
        # Test too short
        response = self.client.put('/users/me', data={'username': 'ab'})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Username must be between 3 and 30 characters', response.data)
        
        # Test too long
        response = self.client.put('/users/me', data={'username': 'a' * 31})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Username must be between 3 and 30 characters', response.data)

    def test_update_profile_duplicate_username(self):
        """Test profile update with already existing username"""        
        # Create another user first
        self.client.post('/auth/register', data={
            'username': 'existing_user',
            'email': 'existing@example.com',
            'password': 'password123'
        })
        
        self.login_user()
        response = self.client.put('/users/me', data={'username': 'existing_user'})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Username already exists', response.data)

    @patch('flask_caching.Cache.delete')
    @patch('api.v1.views.users.invalidate_all')
    def test_delete_user_success(self, mock_invalidate_all, mock_cache_delete):
        """Test successful user deletion"""

        # Register a new user
        response = self.client.post('/auth/register', data={
            'username': 'delete_user',
            'email': 'delete_user@example.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 201)
        delete_id = response.get_json().get("userId")

        # Log in as the newly registered user by setting the session
        with self.client.session_transaction() as session:
            session['user_id'] = delete_id
            session['logged_in'] = True

        # Perform the delete request
        response_delete = self.client.delete(f'/users/{delete_id}')
        
        # Check response status and content
        self.assertEqual(response_delete.status_code, 200)
        self.assertIn(f'User {delete_id} deleted successfully'.encode(), response_delete.data)

        # Verify the user cache deletion
        mock_cache_delete.assert_called_with(f'user_profile:{delete_id}')
        
        # Verify that all relevant caches were invalidated
        mock_invalidate_all.assert_any_call('album')
        mock_invalidate_all.assert_any_call('artist')
        mock_invalidate_all.assert_any_call('music')
        mock_invalidate_all.assert_any_call('playlist')
        mock_invalidate_all.assert_any_call('news')

        # Verify that the session was cleared
        with self.client.session_transaction() as session:
            self.assertNotIn('user_id', session)
            self.assertNotIn('logged_in', session)

    def test_delete_user_unauthorized(self):
        """Test user deletion without login"""
        response = self.client.delete(f'/users/{self.test_user_id}')
        self.assertEqual(response.status_code, 401)
        self.assertIn(b'Unauthorized', response.data)

    def test_delete_nonexistent_user(self):
        """Test deleting a non-existent user"""
        self.login_user()
        response = self.client.delete('/users/nonexistent_id')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'User not found', response.data)

    def test_delete_different_user(self):
        """Test attempting to delete a different user's account"""

        # Register a new user that is different from the logged-in user
        response = self.client.post('/auth/register', data={
            'username': 'delete_another_user',
            'email': 'delete_another_user@example.com',
            'password': 'password123'
        })
        
        self.assertEqual(response.status_code, 201)
        delete_id = response.get_json().get("userId")

        # Log in the first (original) user
        self.login_user()

        # Attempt to delete the newly registered user as the logged-in user
        response = self.client.delete(f'/users/{delete_id}')
        
        # Verify the user cannot delete someone else's account
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'Unauthorized. You can only delete your own account', response.data)

    def test_request_password_reset(self):
        """Test successful password reset request"""
        response = self.client.post('/auth/reset-password', data={
            'email': 'session@example.com'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'reset_token', response.data)

    def test_request_password_reset_missing_email(self):
        """Test password reset request without email"""
        response = self.client.post('/auth/reset-password', data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Email required', response.data)

    def test_request_password_reset_invalid_email(self):
        """Test password reset request with non-existent email"""
        response = self.client.post('/auth/reset-password', data={
            'email': 'nonexistent@example.com'
        })
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'User not found', response.data)

    def test_reset_password_with_token(self):
        """Test password reset confirmation with valid token"""
        # First request a reset token
        response = self.client.post('/auth/reset-password', data={
            'email': 'session@example.com'
        })
        token = response.json['reset_token']
        
        # Test the confirmation
        response = self.client.post('/auth/reset-password/confirm', data={
            'token': token
        })
        self.assertEqual(response.status_code, 302)  # Redirect status

    def test_reset_password_with_invalid_token(self):
        """Test password reset confirmation with invalid token"""
        response = self.client.post('/auth/reset-password/confirm', data={
            'token': 'invalid_token'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Invalid or expired token', response.data)

    def test_change_password_success(self):
        """Test successful password change"""
        # First get a valid token
        response = self.client.post('/auth/reset-password', data={
            'email': 'session@example.com'
        })
        token = response.json['reset_token']
        
        # Test password change
        response = self.client.post(f'/auth/reset-password/change-password?token={token}', data={
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Password reset successfully', response.data)

    def test_change_password_missing_fields(self):
        """Test password change with missing fields"""
        response = self.client.post('/auth/reset-password/change-password?token=sometoken', data={
            'new_password': 'newpassword123'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Missing fields', response.data)

    def test_change_password_mismatch(self):
        """Test password change with mismatched passwords"""
        response = self.client.post('/auth/reset-password/change-password?token=sometoken', data={
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Passwords do not match', response.data)

    def test_get_user_artists_success(self):
        """Test successful retrieval of user's artists"""
        self.login_user()
        response = self.client.get('/users/me/artists')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'artists', response.data)

    def test_get_user_artists_unauthorized(self):
        """Test artists retrieval without login"""
        response = self.client.get('/users/me/artists')
        self.assertEqual(response.status_code, 401)
        self.assertIn(b'No active session', response.data)

    @patch('flask.current_app.cache.get')
    @patch('flask.current_app.cache.set')
    def test_get_user_news_success(self, mock_cache_set, mock_cache_get):
        """Test successful retrieval of user's news"""
        mock_cache_get.return_value = None
        
        self.login_user()
        
        response = self.client.get('/users/me/news')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        self.assertIsNotNone(data)
        self.assertIn('news', data)
        self.assertIn('total', data)
        self.assertEqual(data['total'], 2)
        
        # Verify news content
        news_titles = [news['title'] for news in data['news']]
        self.assertIn('Test News 1', news_titles)
        self.assertIn('Test News 2', news_titles)
        
        # Verify pagination and links
        self.assertIn('_links', data)
        self.assertIn('self', data['_links'])

        # Verify cache interactions
        cache_key = f'user_news:{self.test_user_id}:page_1'
        mock_cache_get.assert_called_once_with(cache_key)
        mock_cache_set.assert_called_once()

    def test_get_user_news_pagination(self):
        """Test news retrieval with pagination"""
        self.login_user()
        
        # Test first page with limit 1
        response = self.client.get('/users/me/news?page=1&limit=1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsNotNone(data, msg=f"Response JSON is None, raw data: {response.data}")
        
        # Assert response structure and pagination
        self.assertEqual(len(data['news']), 1)
        self.assertEqual(data['total'], 2)
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['limit'], 1)
        self.assertIn('_links', data)
        self.assertIn('next', data['_links'])
        self.assertTrue(data['_links']['prev'] is None)
        
        # Test second page
        response = self.client.get('/users/me/news?page=2&limit=1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Assert response structure and pagination for the second page
        self.assertEqual(len(data['news']), 1)
        self.assertIn('prev', data['_links'])
        self.assertTrue(data['_links']['next'] is None or 'next' not in data['_links'])

    def test_get_user_news_unauthorized(self):
        """Test news retrieval without login"""
        response = self.client.get('/users/me/news')
        self.assertEqual(response.status_code, 401)
        self.assertIn(b'No active session', response.data)

    @patch('PIL.Image.open')
    @patch('flask.current_app.cache.delete')
    def test_update_profile_picture_success(self, mock_cache_delete, mock_image_open):
        """Test successful profile picture update"""
        self.login_user()

        # Create test image data within the test function
        with BytesIO() as test_image:
            Image.new('RGB', (200, 200), color='red').save(test_image, 'JPEG')
            test_image.seek(0)

            # Setup mock image processing
            mock_image = Mock()
            mock_image.thumbnail = Mock()
            mock_image.save = Mock()
            mock_image_open.return_value = mock_image

            data = {'file': (test_image, 'test.jpg', 'image/jpeg')}
            
            response = self.client.post(
                '/users/me/profile-picture',
                data=data,
                content_type='multipart/form-data'
            )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['message'], 'Profile picture updated successfully')
        self.assertIn('_links', response_data)
        self.assertIn('self', response_data['_links'])
        
        # Verify mock calls
        expected_path = os.path.join(
            USER_PROFILE_UPLOAD,
            f"{self.test_user_id}_profile.jpg"
        )
        mock_image_open.assert_called_once_with(expected_path)
        mock_image.thumbnail.assert_called_once_with((100, 100))
        mock_cache_delete.assert_called_once_with(f"user_profile:{self.test_user_id}")

    def test_update_profile_picture_no_auth(self):
        """Test profile picture update without authentication"""

        with BytesIO() as test_image:
            Image.new('RGB', (200, 200), color='red').save(test_image, 'JPEG')
            test_image.seek(0)

            data = {'file': (test_image, 'test.jpg', 'image/jpeg')}
            response = self.client.post(
                '/users/me/profile-picture',
                data=data,
                content_type='multipart/form-data'
            )

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'No active session')

    @patch('imghdr.what')
    def test_update_profile_picture_invalid_type(self, mock_imghdr):
        """Test profile picture update with invalid file type"""
        self.login_user()
        mock_imghdr.return_value = 'text'
        
        with BytesIO(b'not an image') as invalid_image_data:
            data = {'file': (invalid_image_data, 'test.txt', 'text/plain')}
            
            response = self.client.post(
                '/users/me/profile-picture',
                data=data,
                content_type='multipart/form-data'
            )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Invalid file type')
 
    @patch('PIL.Image.open')
    def test_update_profile_picture_processing_error(self, mock_image_open):
        """Test profile picture update with image processing error"""
        self.login_user()
        mock_image_open.side_effect = Exception("Processing error")

        # Create test image data within the test function
        with BytesIO() as test_image:
            Image.new('RGB', (200, 200), color='red').save(test_image, 'JPEG')
            test_image.seek(0)

            data = {'file': (test_image, 'test.jpg', 'image/jpeg')}
            response = self.client.post(
                '/users/me/profile-picture',
                data=data,
                content_type='multipart/form-data'
            )
        
        # Verify response
        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Error processing image')

    def test_update_profile_picture_no_file(self):
        """Test profile picture update without file"""
        self.login_user()

        # Make the request without a context manager
        response = self.client.post('/users/me/profile-picture')

        # Verify the response
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'No file uploaded')
