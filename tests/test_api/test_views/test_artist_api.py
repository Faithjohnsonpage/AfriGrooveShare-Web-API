#!/usr/bin/env python3
import unittest
from io import BytesIO
from pathlib import Path
from PIL import Image
import os
import imghdr
from models.user import User
from models.artist import Artist
from models import storage
from sqlalchemy.sql import text
from ..test_base_app import BaseTestCase
from unittest.mock import patch, Mock, call
#from flask_caching import Cache
import flask_caching
from flask import session, json


USER_PROFILE_UPLOAD = 'api/v1/uploads/artist_pics'


class ArtistTestCase(BaseTestCase):
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

        # Create an artist instance
        cls.artist = Artist()
        cls.artist.name = "Test Artist"
        cls.artist.bio = "This is a test artist bio."
        cls.artist.profile_picture_url = "http://example.com/artist.jpg"
        cls.artist.user_id = cls.user.id
        cls.artist.save()
        cls.test_artist_id = cls.artist.id

    @classmethod
    def tearDownClass(cls):
        """Teardown class-level resources"""
        user = storage.get(User, cls.user.id)
        if user:
            user.delete()
            storage.save()

        # Clean up test files
        test_paths = [
            f"{cls.test_artist_id}_profile.jpg",
            f"{cls.test_artist_id}_profile_thumbnail.jpg"
        ]
        for filename in test_paths:
            path = os.path.join(USER_PROFILE_UPLOAD, filename)
            if os.path.exists(path):
                os.remove(path)

    def login_user(self):
        """Helper method to log in the user and set up session"""
        with self.client.session_transaction() as session:
            session['user_id'] = self.test_user_id
            session['logged_in'] = True

    # Create Artist Tests
    @patch('api.v1.views.artist.invalidate_all_artists_cache')
    def test_create_artist(self, mock_cache_invalidate):
        """Test creating a new artist"""
        self.login_user()
        data = {
            'name': "Artist A",
            'bio': "Bio of Test Artist"
        }
        
        response = self.client.post(
            '/artists',
            data=data,
            content_type='multipart/form-data'
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertIn(b"Artist created successfully", response.data)
        mock_cache_invalidate.assert_called_once()
        
        # Verify response structure
        response_data = json.loads(response.data)
        self.assertIn('artistId', response_data)
        self.assertIn('_links', response_data)
        self.assertIn('self', response_data['_links'])

    def test_create_artist_no_auth(self):
        """Test creating artist without authentication"""
        data = {
            'name': "Artist B",
            'bio': "Bio of Test Artist"
        }
        
        response = self.client.post(
            '/artists',
            data=data,
            content_type='multipart/form-data'
        )
        
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'No active session')

    def test_create_artist_missing_name(self):
        """Test creating artist without name"""
        self.login_user()
        data = {
            'bio': "Bio of Test Artist"
        }
        
        response = self.client.post(
            '/artists',
            data=data,
            content_type='multipart/form-data'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Missing name')

    # Get Artist Tests
    @patch('flask_caching.Cache.get')
    @patch('flask_caching.Cache.set')
    def test_get_artist(self, mock_cache_set, mock_cache_get):
        """Test getting an artist by ID"""
        mock_cache_get.return_value = None

        response = self.client.get(f'/artists/{self.test_artist_id}')
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('artist', response_data)
        self.assertEqual(response_data['artist']['name'], "Test Artist")
        self.assertIn('_links', response_data['artist'])

        # Verify cache interactions
        mock_cache_get.assert_called_once()
        mock_cache_set.assert_called_once()

    def test_get_artist_not_found(self):
        """Test getting non-existent artist"""
        response = self.client.get('/artists/nonexistent_id')
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Artist not found')

    # Update Artist Tests
    @patch('flask_caching.Cache.delete')
    @patch('api.v1.views.artist.invalidate_all_artists_cache')
    def test_update_artist(self, mock_cache_invalidate, mock_cache_delete):
        """Test updating an artist"""
        self.login_user()

        # Create a new artist
        artist_data = {
            'name': "Artist C",
            'bio': "Bio of Test Artist"
        }
        create_response = self.client.post(
            '/artists',
            data=artist_data,
            content_type='multipart/form-data'
        )

        # Assert successful creation
        self.assertEqual(create_response.status_code, 201)
        created_artist_id = create_response.json.get("artistId")
        self.assertIsNotNone(created_artist_id)

        data = {
            'name': "Updated Artist Name",
            'bio': "Updated Artist Bio"
        }
        
        # Update the artist
        response = self.client.put(
            f'/artists/{created_artist_id}',
            data=data,
            content_type='multipart/form-data'
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['message'], 'Artist updated successfully')
        self.assertIn('_links', response_data)

        # Verify cache invalidation calls
        mock_cache_invalidate.assert_called()
        
        mock_cache_delete.assert_any_call(f"artist_{created_artist_id}")
        mock_cache_delete.assert_any_call(f"artist_{created_artist_id}_user_{self.test_user_id}")

    def test_update_artist_no_auth(self):
        """Test updating artist without authentication"""
        data = {
            'name': "Updated Artist Name"
        }
        
        response = self.client.put(
            f'/artists/{self.test_artist_id}',
            data=data,
            content_type='multipart/form-data'
        )
        
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'No active session')

    def test_update_artist_not_found(self):
        """Test updating non-existent artist"""
        self.login_user()
        data = {
            'name': "Updated Artist Name"
        }
        
        response = self.client.put(
            '/artists/nonexistent_id',
            data=data,
            content_type='multipart/form-data'
        )
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Artist not found')

    # Delete Artist Tests
    @patch('flask_caching.Cache.delete')
    @patch('api.v1.views.artist.invalidate_all_artists_cache')
    def test_delete_artist(self, mock_cache_invalidate, mock_cache_delete):
        """Test deleting an artist and verifying response links"""
        self.login_user()

        # Create a new artist
        artist_data = {
            'name': "Artist B",
            'bio': "Bio of Test Artist"
        }
        create_response = self.client.post(
            '/artists',
            data=artist_data,
            content_type='multipart/form-data'
        )

        # Assert successful creation
        self.assertEqual(create_response.status_code, 201)
        created_artist_id = create_response.json.get("artistId")
        self.assertIsNotNone(created_artist_id)

        # Delete the created artist
        delete_response = self.client.delete(f'/artists/{created_artist_id}')

        # Assert successful deletion
        self.assertEqual(delete_response.status_code, 200)
        delete_response_data = delete_response.json
        self.assertEqual(delete_response_data['message'], 'Artist deleted successfully')
        self.assertIn('_links', delete_response_data)

        # Verify cache invalidation calls
        mock_cache_invalidate.assert_called()
        
        mock_cache_delete.assert_any_call(f"artist_{created_artist_id}")
        mock_cache_delete.assert_any_call(f"artist_{created_artist_id}_user_{self.test_user_id}")

    def test_delete_artist_no_auth(self):
        """Test deleting artist without authentication"""
        response = self.client.delete(f'/artists/{self.test_artist_id}')
        
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'No active session')

    def test_delete_artist_not_found(self):
        """Test deleting non-existent artist"""
        self.login_user()
        response = self.client.delete('/artists/nonexistent_id')
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Artist not found')

    # List Artists Tests
    @patch('flask_caching.Cache.get')
    @patch('flask_caching.Cache.set')
    def test_list_artists(self, mock_cache_set, mock_cache_get):
        """Test listing all artists"""
        mock_cache_get.return_value = None

        response = self.client.get('/artists')
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('artists', response_data)
        self.assertIn('total', response_data)
        self.assertIn('page', response_data)
        self.assertIn('limit', response_data)
        self.assertIn('_links', response_data)

        # Verify cache interactions
        mock_cache_get.assert_called_once()
        mock_cache_set.assert_called_once()

    @patch('flask_caching.Cache.get')
    @patch('flask_caching.Cache.set')
    def test_list_artists_pagination(self, mock_cache_set, mock_cache_get):
        """Test artists listing pagination"""
        mock_cache_get.return_value = None

        response = self.client.get('/artists?page=1&limit=5')
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('artists', response_data)
        self.assertLessEqual(len(response_data['artists']), 5)

        # Verify cache interactions
        mock_cache_get.assert_called_once()
        mock_cache_set.assert_called_once()

    # Profile Picture Tests
    @patch('PIL.Image.open')
    @patch('flask.current_app.cache.delete')
    def test_update_profile_picture_success(self, mock_cache_delete, mock_image_open):
        """Test successful profile picture update"""
        self.login_user()

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
                f'/artists/{self.test_artist_id}/profile-picture',
                data=data,
                content_type='multipart/form-data'
            )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['message'], 'Profile picture updated successfully')
        self.assertIn('_links', response_data)
        
        mock_image.thumbnail.assert_called_once_with((500, 500))
        mock_cache_delete.assert_called()

    def test_update_profile_picture_no_auth(self):
        """Test profile picture update without authentication"""
        with BytesIO() as test_image:
            Image.new('RGB', (200, 200), color='red').save(test_image, 'JPEG')
            test_image.seek(0)

            data = {'file': (test_image, 'test.jpg', 'image/jpeg')}
            response = self.client.post(
                f'/artists/{self.test_artist_id}/profile-picture',
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
        
        with BytesIO(b'not an image') as invalid_file:
            data = {'file': (invalid_file, 'test.txt', 'text/plain')}
            response = self.client.post(
                f'/artists/{self.test_artist_id}/profile-picture',
                data=data,
                content_type='multipart/form-data'
            )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Invalid file type')

    def test_update_profile_picture_no_file(self):
        """Test profile picture update without file"""
        self.login_user()
        response = self.client.post(f'/artists/{self.test_artist_id}/profile-picture')

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'No file uploaded')

    @patch('PIL.Image.open')
    def test_update_profile_picture_processing_error(self, mock_image_open):
        """Test profile picture update with image processing error"""
        self.login_user()
        mock_image_open.side_effect = Exception("Processing error")

        with BytesIO() as test_image:
            Image.new('RGB', (200, 200), color='red').save(test_image, 'JPEG')
            test_image.seek(0)

            data = {'file': (test_image, 'test.jpg', 'image/jpeg')}
            response = self.client.post(
                f'/artists/{self.test_artist_id}/profile-picture',
                data=data,
                content_type='multipart/form-data'
            )
        
        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Error processing image')
