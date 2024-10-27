#!/usr/bin/env python3
import unittest
from io import BytesIO
from pathlib import Path
from PIL import Image
import os
import imghdr
from models.user import User
from models.artist import Artist
from models.album import Album
from models import storage
from sqlalchemy.sql import text
from ..test_base_app import BaseTestCase
from unittest.mock import patch, Mock
from flask_caching import Cache
from flask import session, json
from datetime import datetime


ALBUM_COVER_UPLOAD = 'api/v1/uploads/album_cover'


class AlbumTestCase(BaseTestCase):

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

        # Create an album instance
        cls.album = Album()
        cls.album.title = "Test Album"
        cls.album.artist_id = cls.artist.id
        cls.album.release_date = datetime.strptime("2024-01-01", "%Y-%m-%d").date()
        cls.album.cover_image_url = "http://example.com/image.jpg"
        cls.album.description = "This is a test album description."
        cls.album.save()
        cls.test_album_id = cls.album.id

        # Create another user and artist
        cls.other_user = User()
        cls.other_user.username = "other_user"
        cls.other_user.email = "other@test.com"
        cls.other_user.password = "test123"
        cls.other_user.save()
        cls.test_other_user_id = cls.other_user.id

        cls.other_artist = Artist()
        cls.other_artist.name = "Other Artist"
        cls.other_artist.bio = "This is the other artist bio."
        cls.other_artist.user_id = cls.other_user.id
        cls.other_artist.save()
        cls.test_other_artist_id = cls.other_artist.id

    @classmethod
    def tearDownClass(cls):
        """Teardown class-level resources"""
        users_to_delete = [
            'session@example.com',
            'other@test.com'
        ]
        for email in users_to_delete:
            user = storage.filter_by(User, email=email)
            if user:
                storage.delete(user)
        storage.save()

        # Clean up test file
        test_path = os.path.join(ALBUM_COVER_UPLOAD, f"{cls.test_album_id}_cover.jpg")
        if os.path.exists(test_path):
            os.remove(test_path)

    def login_user(self):
        """Helper method to log in the user and set up session"""
        with self.client.session_transaction() as session:
            session['user_id'] = self.test_user_id
            session['logged_in'] = True

    @patch('api.v1.views.album.invalidate_all_albums_cache')
    def test_create_album(self, mock_cache_invalidate):
        """Test creating a new album and cache invalidation"""
        self.login_user()

        # Prepare request data
        data = {
            'title': "Test Album",
            'release_date': "2024-09-13",
            'description': 'New Album Description'
        }

        # Send POST request to create an album
        response = self.client.post(
            f'/albums?artist_id={self.test_artist_id}',
            data=data,
        )

        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertIn('message', response_data)
        self.assertEqual(response_data['message'], 'Album created successfully')
        self.assertIn('albumId', response_data)
        self.assertIn('_links', response_data)

        # Verify that cache invalidation was called
        mock_cache_invalidate.assert_called_once()

    def test_create_album_no_auth(self):
        """Test album creation without authentication"""
        data = {
            'title': 'Test Album',
            'description': 'Test Description',
            'release_date': '2024-01-01'
        }

        response = self.client.post(
            f'/albums?artist_id={self.test_artist_id}',
            data=data
        )

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'No active session')

    def test_create_album_invalid_artist(self):
        """Test album creation with invalid artist ID"""
        self.login_user()

        data = {
            'title': 'Test Album',
            'description': 'Test Description',
            'release_date': '2024-01-01'
        }

        response = self.client.post(
            '/albums?artist_id=invalid_id',
            data=data
        )

        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Artist not found')

    def test_create_album_unauthorized_artist(self):
        """Test album creation for unauthorized artist"""
        # Create another user and artist
        
        self.login_user()

        data = {
            'title': 'Test Album',
            'description': 'Test Description',
            'release_date': '2024-01-01'
        }

        response = self.client.post(
            f'/albums?artist_id={self.test_other_artist_id}',
            data=data
        )

        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Unauthorized')

    def test_create_album_missing_title(self):
        """Test album creation without title"""
        self.login_user()

        data = {
            'description': 'Test Description',
            'release_date': '2024-01-01'
        }

        response = self.client.post(
            f'/albums?artist_id={self.test_artist_id}',
            data=data
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Missing album title')

    def test_create_album_invalid_date(self):
        """Test album creation with invalid release date"""
        self.login_user()

        data = {
            'title': 'Test Album',
            'description': 'Test Description',
            'release_date': 'invalid-date'
        }

        response = self.client.post(
            f'/albums?artist_id={self.test_artist_id}',
            data=data
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Invalid release date format, use YYYY-MM-DD')

    @patch('flask_caching.Cache.get')
    @patch('flask_caching.Cache.set')
    def test_get_album_success(self, mock_cache_set, mock_cache_get):
        """Test successful album retrieval"""
        
        mock_cache_get.return_value = None

        response = self.client.get(f'/albums/{self.test_album_id}')

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('album', response_data)
        self.assertEqual(response_data['album']['title'], 'Test Album')
        self.assertEqual(response_data['album']['artist']['id'], self.test_artist_id)

        # Verify cache interactions
        cache_key = f'album_{self.test_album_id}'
        mock_cache_get.assert_called_once_with(cache_key)
        mock_cache_set.assert_called_once()

    def test_get_album_not_found(self):
        """Test album retrieval with invalid ID"""
        response = self.client.get('/albums/invalid_id')

        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Album not found')

    def test_list_albums(self):
        """Test listing albums"""
        response = self.client.get('/albums')

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('albums', response_data)
        self.assertEqual(len(response_data['albums']), 2)
        self.assertEqual(response_data['total'], 2)

    def test_list_albums_pagination(self):
        """Test album listing with pagination"""
        
        # Test first page
        response = self.client.get('/albums?page=1&limit=1')

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(len(response_data['albums']), 1)
        self.assertEqual(response_data['total'], 2)
        self.assertEqual(response_data['page'], 1)
        self.assertIsNotNone(response_data['_links']['next'])
        self.assertIsNone(response_data['_links']['prev'])

        # Test second page
        response = self.client.get('/albums?page=2&limit=1')

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(len(response_data['albums']), 1)
        self.assertIsNone(response_data['_links']['next'])
        self.assertIsNotNone(response_data['_links']['prev'])

    @patch('PIL.Image.open')
    @patch('flask.current_app.cache.delete')
    def test_update_album_cover_success(self, mock_cache_delete, mock_image_open):
        """Test successful album cover update"""
        self.login_user()

        # Create test image
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
                f'/albums/{self.test_album_id}/cover-image',
                data=data,
                content_type='multipart/form-data'
            )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['message'], 'Cover image updated successfully')
        self.assertIn('_links', response_data)

        mock_image_open.assert_called_once()
        mock_image.thumbnail.assert_called_once()
        mock_cache_delete.assert_called_once()

    def test_update_album_cover_no_auth(self):
        """Test album cover update without authentication"""

        with BytesIO() as test_image:
            Image.new('RGB', (200, 200), color='red').save(test_image, 'JPEG')
            test_image.seek(0)

            data = {'file': (test_image, 'test.jpg', 'image/jpeg')}
            response = self.client.post(
                f'/albums/{self.test_album_id}/cover-image',
                data=data,
                content_type='multipart/form-data'
            )

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'No active session')

    @patch('imghdr.what')
    def test_update_album_cover_invalid_type(self, mock_imghdr):
        """Test album cover update with invalid file type"""
        self.login_user()

        mock_imghdr.return_value = 'text'

        with BytesIO(b'not an image') as invalid_image_data:
            data = {'file': (invalid_image_data, 'test.txt', 'text/plain')}

            response = self.client.post(
                f'/albums/{self.test_album_id}/cover-image',
                data=data,
                content_type='multipart/form-data'
            )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Invalid file type')

    def test_update_album_cover_no_file(self):
        """Test album cover update without file"""
        self.login_user()

        response = self.client.post(f'/albums/{self.test_album_id}/cover-image')

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'No file uploaded')

    @patch('PIL.Image.open')
    def test_update_album_cover_processing_error(self, mock_image_open):
        """Test album cover update with image processing error"""
        self.login_user()

        mock_image_open.side_effect = Exception("Processing error")

        with BytesIO() as test_image:
            Image.new('RGB', (200, 200), color='red').save(test_image, 'JPEG')
            test_image.seek(0)

            data = {'file': (test_image, 'test.jpg', 'image/jpeg')}
            response = self.client.post(
                f'/albums/{self.test_album_id}/cover-image',
                data=data,
                content_type='multipart/form-data'
            )

        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Error processing image') 
