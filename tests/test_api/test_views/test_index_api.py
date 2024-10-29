#!/usr/bin/env python3
import unittest
from unittest.mock import patch
from models import storage
from models.user import User
from models.artist import Artist
from models.album import Album
from models.music import Music
from models.news import News
from models.playlist import Playlist
from ..test_base_app import BaseTestCase
from datetime import datetime

class StatusAndStatsTestCase(BaseTestCase):
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

        cls.news1 = News()
        cls.news1.title = "Test News 1"
        cls.news1.content = "This is the first test news content."
        cls.news1.author = "John Doe"
        cls.news1.category = "Music Technology"
        cls.news1.user_id = cls.user.id
        storage.new(cls.news1)
        storage.save()

    @classmethod
    def tearDownClass(cls):
        """Teardown class-level resources"""
        user = storage.get(User, cls.user.id)
        if user:
            user.delete()
            storage.save()
    
    @patch('api.v1.views.get_limiter', return_value=None)
    def test_status_endpoint(self, mock_limiter):
        """Test the /status endpoint returns the expected response"""
        response = self.client.get('/status')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(data, {"status": "OK"})

    @patch('api.v1.views.get_limiter', return_value=None)
    def test_stats_endpoint(self, mock_limiter):
        """Test the /stats endpoint returns the correct counts"""
                
        response = self.client.get('/stats')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        
        # Validate counts for each object type
        self.assertEqual(data["users"], storage.count(User))
        self.assertEqual(data["artists"], storage.count(Artist))
        self.assertEqual(data["albums"], storage.count(Album))
        self.assertEqual(data["music"], storage.count(Music))
        self.assertEqual(data["playlists"], storage.count(Playlist))
        self.assertEqual(data["news"], storage.count(News))
