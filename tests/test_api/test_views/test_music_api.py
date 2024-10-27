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
from models.music import Music, ReleaseType
from models.genre import Genre
from models import storage
from sqlalchemy.sql import text
from ..test_base_app import BaseTestCase
from unittest.mock import patch, Mock
from flask_caching import Cache
from flask import session, json
from datetime import datetime


MUSIC_COVER_UPLOAD = 'api/v1/uploads/music_cover'
UPLOAD_FOLDER = 'api/v1/uploads/music'


class MusicTestCase(BaseTestCase):

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

        # Create a genre instance
        cls.genre = Genre()
        cls.genre.name = "Pop"
        cls.genre.save()

        # Create a music instance for a single track
        cls.music = Music()
        cls.music.title = "Bohemian Rhapsody"
        cls.music.artist_id = cls.artist.id
        cls.music.genre_id = cls.genre.id
        cls.music.file_url = "https://example.com/music/bohemian_rhapsody.mp3"
        cls.music.duration = 354
        cls.music.release_date = datetime.strptime("1975-10-31", "%Y-%m-%d").date()
        cls.music.cover_image_url = "http://example.com/music/bohemian_rhapsody_cover.jpg"
        cls.music.description = "A test description for the music track."
        cls.music.release_type = ReleaseType.SINGLE
        cls.music.save()
        cls.test_music_id = cls.music.id

    @classmethod
    def tearDownClass(cls):
        """Teardown class-level resources"""
        users_to_delete = [
            'session@example.com'
        ]
        for email in users_to_delete:
            user = storage.filter_by(User, email=email)
            if user:
                storage.delete(user)
        storage.save()

        genre = storage.get(Genre, cls.genre.id)
        if genre:
            genre.delete()
            storage.save()

        # Clean up test cover image file
        test_path = os.path.join(MUSIC_COVER_UPLOAD, f"{cls.test_music_id}_cover.jpg")
        if os.path.exists(test_path):
            os.remove(test_path)

        # Clean up test music file
        test_path = os.path.join(UPLOAD_FOLDER, 'test.mp3')
        if os.path.exists(test_path):
            os.remove(test_path)

    def login_user(self):
        """Helper method to log in the user and set up session"""
        with self.client.session_transaction() as session:
            session['user_id'] = self.test_user_id
            session['logged_in'] = True

    def create_test_mp3(self):
        """Helper method to create a test MP3 file"""
        test_file = BytesIO(b"ID3\x03\x00\x00\x00\x00\x0F\x76")
        test_file.name = "test.mp3"
        return test_file

    @patch('api.v1.views.music.invalidate_all_music_cache')
    def test_upload_music_success_single(self, mock_cache_invalidate):
        """Test successful music upload"""
        self.login_user()

        test_file = self.create_test_mp3()

        data = {
            'title': 'Test Upload',
            'description': 'Test Description',
            'genre': 'Pop',
            'artist': 'Test Artist',
            'duration': '3:00',
            'release_date': '2024-01-01',
            'file': (test_file, 'test.mp3')
        }

        response = self.client.post(
            '/music/upload',
            data=data,
            content_type='multipart/form-data'
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn('musicId', response.json)

        mock_cache_invalidate.assert_called_once()

    @patch('api.v1.views.music.invalidate_all_music_cache')
    def test_upload_music_success_album(self, mock_cache_invalidate):
        """Test successful music upload for album"""
        self.login_user()

        test_file = self.create_test_mp3()

        data = {
            'title': 'Test Upload',
            'description': 'Test Description',
            'genre': 'Pop',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'duration': '3:00',
            'release_date': '2024-01-01',
            'file': (test_file, 'test.mp3')
        }

        response = self.client.post(
            '/music/upload',
            data=data,
            content_type='multipart/form-data'
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn('musicId', response.json)

        mock_cache_invalidate.assert_called_once()


    def test_upload_music_no_auth(self):
        """Test music upload without authentication"""
        test_file = self.create_test_mp3()
        data = {
            'title': 'Test Upload',
            'description': 'Test Description',
            'genre': 'Pop',
            'artist': 'Test Artist',
            'duration': '3:00',
            'release_date': '2024-01-01',
            'file': (test_file, 'test.mp3')
        }
        response = self.client.post(
            '/music/upload',
            data=data,
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json['error'], 'No active session')

    def test_upload_music_invalid_artist(self):
        """Test music upload with non-existent artist"""
        self.login_user()
        test_file = self.create_test_mp3()
        data = {
            'title': 'Test Upload',
            'description': 'Test Description',
            'genre': 'Pop',
            'artist': 'Non Existent Artist',
            'duration': '3:00',
            'release_date': '2024-01-01',
            'file': (test_file, 'test.mp3')
        }
        response = self.client.post(
            '/music/upload',
            data=data,
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Artist not found')

    def test_upload_music_missing_required_fields(self):
        """Test music upload with missing required fields"""
        self.login_user()
        test_file = self.create_test_mp3()
        data = {
            'description': 'Test Description',
            'file': (test_file, 'test.mp3')
        }
        response = self.client.post(
            '/music/upload',
            data=data,
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'Missing required fields')

    @patch('mimetypes.guess_type')
    def test_upload_music_invalid_file_type(self, mock_guess_type):
        """Test music upload with invalid file type"""
        self.login_user()
        mock_guess_type.return_value = ('audio/wav', None)
        test_file = BytesIO(b"fake wav data")
        test_file.name = "test.wav"
        
        data = {
            'title': 'Test Upload',
            'description': 'Test Description',
            'genre': 'Pop',
            'artist': 'Test Artist',
            'duration': '3:00',
            'release_date': '2024-01-01',
            'file': (test_file, 'test.wav')
        }
        response = self.client.post(
            '/music/upload',
            data=data,
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'Invalid file type, only MP3 is allowed')

    def test_upload_music_invalid_duration_format(self):
        """Test music upload with invalid duration format"""
        self.login_user()
        test_file = self.create_test_mp3()
        data = {
            'title': 'Test Upload',
            'description': 'Test Description',
            'genre': 'Pop',
            'artist': 'Test Artist',
            'duration': 'invalid',
            'release_date': '2024-01-01',
            'file': (test_file, 'test.mp3')
        }
        response = self.client.post(
            '/music/upload',
            data=data,
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'Invalid duration format. Use MM:SS.')

    def test_upload_music_invalid_release_date_format(self):
        """Test music upload with invalid release date format"""
        self.login_user()
        test_file = self.create_test_mp3()
        data = {
            'title': 'Test Upload',
            'description': 'Test Description',
            'genre': 'Pop',
            'artist': 'Test Artist',
            'duration': '03:30',  # Valid duration format
            'release_date': 'invalid-date',  # Invalid release date format
            'file': (test_file, 'test.mp3')
        }
        response = self.client.post(
            '/music/upload',
            data=data,
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'Invalid release date format. Use YYYY-MM-DD.')

    @patch('flask.current_app.cache.set')
    @patch('flask.current_app.cache.get')
    def test_get_music_metadata_success(self, mock_cache_get, mock_cache_set):
        """Test successful retrieval of music metadata"""
        mock_cache_get.return_value = None
         
        response = self.client.get(f'/music/{self.test_music_id}')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['title'], 'Bohemian Rhapsody')
        self.assertEqual(response.json['artist'], 'Test Artist')
        self.assertEqual(response.json['duration'], '5:54')
        self.assertEqual(response.json['releaseDate'], '1975-10-31')

        # Verify cache interactions
        mock_cache_get.assert_called_once()
        mock_cache_set.assert_called_once()

    def test_get_music_metadata_not_found(self):
        """Test getting metadata for non-existent music"""
        response = self.client.get('/music/nonexistent-id')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Music not found')

    @patch('flask.current_app.cache.set')
    @patch('flask.current_app.cache.get')
    def test_list_music_files_success(self, mock_cache_get, mock_cache_set):
        """Test successful listing of music files"""
        mock_cache_get.return_value = None
        
        response = self.client.get('/music')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('music', response.json)
        self.assertIn('total', response.json)
        self.assertIn('page', response.json)
        self.assertIn('limit', response.json)
        self.assertIn('_links', response.json)

        # Verify cache interactions
        mock_cache_get.assert_called_once()
        mock_cache_set.assert_called_once()

    def test_list_music_files_with_filters(self):
        """Test listing music files with filters"""
        response = self.client.get('/music?genre=Pop&artist=Test Artist')
        self.assertEqual(response.status_code, 200)
        self.assertIn('music', response.json)

    def test_search_music_success(self):
        """Test successful music search"""
        response = self.client.post('/music/search', 
                                  data='Bohemian Rhapsody',
                                  content_type='text/plain')
        self.assertEqual(response.status_code, 200)

    def test_search_music_no_query(self):
        """Test music search with no query"""
        response = self.client.post('/music/search', 
                                  data='',
                                  content_type='text/plain')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'No search query provided')

    @patch('PIL.Image.open')
    @patch('flask.current_app.cache.delete')
    def test_update_music_cover_image_success(self, mock_cache_delete, mock_image_open):
        """Test successful music cover image update"""
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
                f'/music/{self.test_music_id}/cover-image',
                data=data,
                content_type='multipart/form-data'
            )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Cover image updated successfully')
        self.assertIn('_links', response.json)

        mock_image_open.assert_called_once()
        mock_image.thumbnail.assert_called_once()
        mock_cache_delete.assert_called_once()

    def test_update_music_cover_image_no_auth(self):
        """Test music cover image update without authentication"""
        with BytesIO() as test_image:
            Image.new('RGB', (200, 200), color='red').save(test_image, 'JPEG')
            test_image.seek(0)

            data = {'file': (test_image, 'test.jpg', 'image/jpeg')}
            response = self.client.post(
                '/music/nonexistent-id/cover-image',
                data=data,
                content_type='multipart/form-data'
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json['error'], 'No active session')

    @patch('imghdr.what')
    def test_update_music_cover_invalid_type(self, mock_imghdr):
        """Test music cover image update with invalid file type"""
        self.login_user()
        
        mock_imghdr.return_value = 'text'
        
        with BytesIO(b'not an image') as invalid_image:
            data = {'file': (invalid_image, 'test.txt', 'text/plain')}
            response = self.client.post(
                f'/music/{self.test_music_id}/cover-image',
                data=data,
                content_type='multipart/form-data'
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'Invalid file type')

    def test_update_music_cover_no_file(self):
        """Test music cover image update without a file"""
        self.login_user()
        response = self.client.post(f'/music/{self.test_music_id}/cover-image')

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'No file uploaded')

    @patch('PIL.Image.open')
    def test_update_music_cover_processing_error(self, mock_image_open):
        """Test music cover image update with image processing error"""
        self.login_user()
        mock_image_open.side_effect = Exception("Processing error")

        with BytesIO() as test_image:
            Image.new('RGB', (200, 200), color='red').save(test_image, 'JPEG')
            test_image.seek(0)

            data = {'file': (test_image, 'test.jpg', 'image/jpeg')}
            response = self.client.post(
                f'/music/{self.test_music_id}/cover-image',
                data=data,
                content_type='multipart/form-data'
            )

        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Error processing image')
 
    def test_stream_music_not_found(self):
        """Test streaming non-existent music"""
        response = self.client.get('/music/nonexistent-id/stream')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Music file not found')
