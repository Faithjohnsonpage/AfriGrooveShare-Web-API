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
        cls.album.release_date = "2024-01-01"
        cls.album.cover_image_url = "http://example.com/image.jpg"
        cls.album.description = "This is a test album description."
        cls.album.save()
        cls.test_album_id = cls.album.id

    @classmethod
    def tearDownClass(cls):
        """Teardown class-level resources"""
        user = storage.get(User, cls.user.id)
        if user:
            user.delete()
            storage.save()

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

