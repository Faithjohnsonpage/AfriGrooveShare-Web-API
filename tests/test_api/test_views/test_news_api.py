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


UPLOAD_FOLDER = 'api/v1/uploads/news_cover'


class NewsTestCase(BaseTestCase):

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
        user = storage.get(User, cls.user.id)
        if user:
            user.delete()
            storage.save()

        file_path = os.path.join(UPLOAD_FOLDER, f"{cls.test_news1_id}_test-uuid.jpg")
        if os.path.exists(file_path):
            os.remove(file_path)

    def login_user(self):
        """Helper method to log in the user and set up session"""
        with self.client.session_transaction() as session:
            session['user_id'] = self.test_user_id
            session['logged_in'] = True

    @patch('api.v1.views.news.invalidate_user_news_cache')
    @patch('api.v1.views.news.invalidate_all_news_cache')
    def test_create_news(self, mock_cache_invalidate_all, mock_cache_invalidate_news):
        """Test create news success"""
        self.login_user()

        data = {
            'title': 'Test News',
            'content': 'word ' * 500,
            'category': 'Album Release'
        }
        response = self.client.post('/news', data=data)
        self.assertEqual(response.status_code, 201)
        self.assertIn('newsId', response.json)

        # Verify cache invalidation calls
        mock_cache_invalidate_all.assert_called_once()
        mock_cache_invalidate_news.assert_called_with(self.test_user_id)

    def test_create_news_no_auth(self):
        """Test news creation without authentication"""
        data = {
            'title': 'Test News',
            'content': 'word ' * 500,
            'category': 'Album Release'
        }
        response = self.client.post('/news', data=data)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json['error'], 'No active session')

    def test_create_news_invalid_category(self):
        """Test news creation with invalid category"""
        self.login_user()
        data = {
            'title': 'Test News',
            'content': 'word ' * 500,
            'category': 'Invalid Category'
        }
        response = self.client.post('/news', data=data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'Invalid category')

    def test_create_news_short_content(self):
        """Test news creation with content less than 500 words"""
        self.login_user()
        data = {
            'title': 'Test News',
            'content': 'short content',
            'category': 'Album Release'
        }
        response = self.client.post('/news', data=data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'Content must be at least 500 words.')

    @patch('flask_caching.Cache.get')
    @patch('flask_caching.Cache.set')
    def test_get_news_success(self, mock_cache_set, mock_cache_get):
        """Test successful news retrieval"""
        mock_cache_get.return_value = None
        response = self.client.get(f'/news/{self.test_news1_id}')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('news', response.json)
        self.assertIn('_links', response.json['news'])
        
        # Verify cache interactions
        mock_cache_get.assert_called_once()
        mock_cache_set.assert_called_once()

    def test_get_news_not_found(self):
        """Test getting non-existent news"""
        response = self.client.get('/news/nonexistent_id')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'News not found')

    @patch('api.v1.views.news.invalidate_user_news_cache')
    @patch('api.v1.views.news.invalidate_all_news_cache')
    def test_update_news_success(self, mock_cache_invalidate_all, mock_cache_invalidate_news):
        """Test successful news update"""
        self.login_user()
        data = {
            'title': 'Updated Title',
            'content': 'word ' * 500
        }
        response = self.client.put(
            f'/news/{self.test_news1_id}',
            json=data
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)
        self.assertIn('_links', response.json)

        # Verify cache invalidation
        mock_cache_invalidate_all.assert_called_once()
        mock_cache_invalidate_news.assert_called_with(self.test_user_id)

    def test_update_news_no_auth(self):
        """Test news update without authentication"""
        data = {'title': 'Updated Title'}
        response = self.client.put(
            f'/news/{self.test_news1_id}',
            json=data
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json['error'], 'No active session')

    @patch('api.v1.views.news.invalidate_user_news_cache')
    @patch('api.v1.views.news.invalidate_all_news_cache')
    def test_delete_news_success(self, mock_cache_invalidate_all, mock_cache_invalidate_news):
        """Test successful news deletion"""
        self.login_user()
        response = self.client.delete(f'/news/{self.test_news2_id}')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)
        self.assertIn('_links', response.json)

        # Verify cache invalidation
        mock_cache_invalidate_all.assert_called_once()
        mock_cache_invalidate_news.assert_called_with(self.test_user_id)

    def test_delete_news_no_auth(self):
        """Test news deletion without authentication"""
        response = self.client.delete(f'/news/{self.test_news1_id}')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json['error'], 'No active session')

    @patch('flask_caching.Cache.get')
    @patch('flask_caching.Cache.set')
    def test_list_news(self, mock_cache_set, mock_cache_get):
        """Test listing all news"""
        mock_cache_get.return_value = None

        response = self.client.get('/news')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('news', response.json)
        self.assertIn('total', response.json)
        self.assertIn('page', response.json)
        self.assertIn('limit', response.json)
        self.assertIn('_links', response.json)

        # Verify cache interactions
        mock_cache_get.assert_called_once()
        mock_cache_set.assert_called_once()

    @patch('flask_caching.Cache.get')
    @patch('flask_caching.Cache.set')
    def test_list_news_pagination(self, mock_cache_set, mock_cache_get):
        """Test news listing pagination"""
        mock_cache_get.return_value = None

        response = self.client.get('/news?page=1&limit=5')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('news', response.json)
        self.assertLessEqual(len(response.json['news']), 5)

        # Verify cache interactions
        mock_cache_get.assert_called_once()
        mock_cache_set.assert_called_once()

    @patch('uuid.uuid4')
    @patch('PIL.Image.open')
    @patch('flask.current_app.cache.delete')
    @patch('api.v1.views.news.invalidate_user_news_cache')
    @patch('api.v1.views.news.invalidate_all_news_cache')
    def test_upload_news_image_success(
            self, 
            mock_invalidate_all_cache,
            mock_invalidate_user_cache,
            mock_cache_delete,
            mock_image_open,
            mock_uuid
        ):
        """Test successful news image upload"""
        # Mock UUID to have a predictable filename
        mock_uuid.return_value.hex = 'test-uuid'

        self.login_user()

        # Prepare test image in memory
        with BytesIO() as test_image:
            Image.new('RGB', (200, 200), color='red').save(test_image, 'JPEG')
            test_image.seek(0)

            # Setup mock image processing
            mock_image = Mock()
            mock_image.save = Mock()
            mock_image_open.return_value = mock_image

            data = {'file': (test_image, 'test.jpg', 'image/jpeg')}

            response = self.client.post(
                f'/news/{self.test_news1_id}/image',
                data=data,
                content_type='multipart/form-data'
            )

        self.assertEqual(response.status_code, 201)
        self.assertIn('message', response.json)
        self.assertIn('_links', response.json)

        mock_cache_delete.assert_called()
        mock_invalidate_user_cache.assert_called_once()
        mock_invalidate_all_cache.assert_called_once()

    def test_upload_news_image_no_auth(self):
        """Test news image upload without authentication"""
        with BytesIO() as test_image:
            Image.new('RGB', (200, 200), color='red').save(test_image, 'JPEG')
            test_image.seek(0)

            data = {'file': (test_image, 'test.jpg', 'image/jpeg')}
            response = self.client.post(
                f'/news/{self.test_news1_id}/image',
                data=data,
                content_type='multipart/form-data'
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json['error'], 'No active session')

    @patch('imghdr.what')
    def test_upload_news_image_invalid_type(self, mock_imghdr):
        """Test news image upload with invalid file type"""
        self.login_user()
        mock_imghdr.return_value = 'text'
        
        with BytesIO(b'not an image') as invalid_file:
            data = {'file': (invalid_file, 'test.txt', 'text/plain')}
            response = self.client.post(
                f'/news/{self.test_news1_id}/image',
                data=data,
                content_type='multipart/form-data'
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_upload_news_image_no_file(self):
        """Test news image upload without file"""
        self.login_user()
        response = self.client.post(f'/news/{self.test_news1_id}/image')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'No file uploaded') 
