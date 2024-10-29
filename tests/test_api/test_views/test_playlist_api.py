#!/usr/bin/env python3
import unittest
from pathlib import Path
import os
from models.user import User
from models.artist import Artist
from models.album import Album
from models.genre import Genre
from models.music import Music, ReleaseType
from models.playlist import Playlist
from models import storage
from sqlalchemy.sql import text
from ..test_base_app import BaseTestCase
from unittest.mock import patch, Mock
from flask_caching import Cache
from flask import session, json
from datetime import datetime


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

        # Create a different user
        cls.other_user = User()
        cls.other_user.username = "other_user"
        cls.other_user.email = "other@example.com"
        cls.other_user.password = "password123"
        cls.other_user.save()
        cls.other_user.id

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

        # Create a music instance for an album track
        cls.album_music = Music()
        cls.album_music.title = "Love of My Life"
        cls.album_music.artist_id = cls.artist.id
        cls.album_music.genre_id = cls.genre.id
        cls.album_music.file_url = "https://example.com/music/love_of_my_life.mp3"
        cls.album_music.duration = 210
        cls.album_music.release_date = datetime.strptime("1975-11-21", "%Y-%m-%d").date()
        cls.album_music.cover_image_url = "http://example.com/music/love_of_my_life_cover.jpg"
        cls.album_music.description = "A beautiful ballad dedicated to Freddie Mercury's lover."
        cls.album_music.release_type = ReleaseType.ALBUM
        cls.album_music.album_id = cls.album.id
        cls.album_music.save()
        cls.test_album_music_id = cls.album_music.id

        # Create a playlist instance
        cls.playlist = Playlist()
        cls.playlist.name = "My Rock Playlist"
        cls.playlist.description = "Best rock songs"
        cls.playlist.user_id = cls.test_user_id
        cls.playlist.save()
        cls.test_playlist_id = cls.playlist.id

        # Create another playlist instance
        cls.playlist_1 = Playlist()
        cls.playlist_1.name = "My Pop Playlist"
        cls.playlist_1.description = "Best Pop songs"
        cls.playlist_1.user_id = cls.test_user_id
        cls.playlist_1.save()
        cls.test_playlist_1_id = cls.playlist_1.id

    @classmethod
    def tearDownClass(cls):
        """Teardown class-level resources"""
        users_to_delete = [
            'session@example.com',
            'other@example.com'
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


    def login_user(self):
        """Helper method to log in the user and set up session"""
        with self.client.session_transaction() as session:
            session['user_id'] = self.test_user_id
            session['logged_in'] = True

    @patch('api.v1.views.playlist.invalidate_all_playlists_cache')
    def test_create_playlist(self, mock_cache_invalidate):
        """Test playlist creation"""
        self.login_user()
        response = self.client.post('/playlist/create', data={
            'name': 'New Test Playlist',
            'description': 'New Test Description'
        })
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('playlistId', data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Playlist created successfully')
        mock_cache_invalidate.assert_called_once()

    def test_create_playlist_no_auth(self):
        """Test creating playlist without authentication"""
        data = {
            'name': "Test Playlist",
            'description': "Test Description"
        }
        
        response = self.client.post(
            '/playlist/create',
            data=data
        )
        
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'No active session')

    def test_create_playlist_missing_name(self):
        """Test creating playlist without name"""
        self.login_user()
        data = {
            'description': "Test Description"
        }
        
        response = self.client.post(
            '/playlist/create',
            data=data
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Missing name')

    @patch('flask_caching.Cache.get')
    @patch('flask_caching.Cache.set')
    def test_get_playlist(self, mock_cache_set, mock_cache_get):
        """Test getting a playlist by ID"""
        mock_cache_get.return_value = None
        response = self.client.get(f'/playlists/{self.test_playlist_id}')
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('playlist', response_data)
        self.assertEqual(response_data['playlist']['name'], "My Rock Playlist")
        self.assertIn('_links', response_data['playlist'])

        # Verify cache interactions
        mock_cache_get.assert_called_once()
        mock_cache_set.assert_called_once()

    def test_get_playlist_not_found(self):
        """Test getting non-existent playlist"""
        response = self.client.get('/playlists/nonexistent_id')
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Playlist not found')

    @patch('flask_caching.Cache.delete')
    @patch('api.v1.views.playlist.invalidate_all_playlists_cache')
    def test_update_playlist_edit(self, mock_cache_invalidate, mock_cache_delete):
        """Test updating playlist details"""
        self.login_user()
        data = {
            'action': 'edit',
            'name': "Updated Playlist Name",
            'description': "Updated Description"
        }

        response = self.client.post(
            f'/playlists/{self.test_playlist_id}',
            data=data
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['message'], 'Playlist updated successfully')
        self.assertIn('_links', response_data)
        # Verify cache invalidation calls
        mock_cache_invalidate.assert_called()
        mock_cache_delete.assert_any_call(f"playlist_{self.test_playlist_id}")
        mock_cache_delete.assert_any_call(f"playlist_{self.test_playlist_id}_user_{self.test_user_id}")

    def test_update_playlist_no_auth(self):
        """Test updating playlist without authentication"""
        data = {
            'action': 'edit',
            'name': "Updated Name"
        }

        response = self.client.post(
            f'/playlists/{self.test_playlist_id}',
            data=data
        )

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'No active session')

    def test_update_playlist_unauthorized(self):
        """Test updating playlist by non-owner"""
        # Login as different user
        with self.client.session_transaction() as session:
            session['user_id'] = self.other_user.id
            session['logged_in'] = True

        data = {
            'action': 'edit',
            'name': "Unauthorized Update"
        }

        response = self.client.post(
            f'/playlists/{self.test_playlist_id}',
            data=data
        )

        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Unauthorized to update this playlist')

    @patch('flask_caching.Cache.delete')
    @patch('api.v1.views.playlist.invalidate_all_playlists_cache')
    def test_add_music_to_playlist(self, mock_cache_invalidate, mock_cache_delete):
        """Test adding music to playlist"""
        self.login_user()
        data = {
            'action': 'add_music',
            'musicIds': self.test_music_id,
            'musicIds': self.test_album_music_id
        }

        response = self.client.post(
            f'/playlists/{self.test_playlist_id}',
            data=data
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['message'], 'Music added to playlist successfully')
        self.assertIn('_links', response_data)

        # Verify cache invalidation calls
        mock_cache_invalidate.assert_called()
        mock_cache_delete.assert_any_call(f"playlist_{self.test_playlist_id}")
        mock_cache_delete.assert_any_call(f"playlist_{self.test_playlist_id}_user_{self.test_user_id}")

    def test_add_invalid_music_to_playlist(self):
        """Test adding non-existent music to playlist"""
        self.login_user()
        data = {
            'action': 'add_music',
            'musicIds': ['nonexistent_music_id']
        }

        response = self.client.post(
            f'/playlists/{self.test_playlist_id}',
            data=data
        )

        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Music with id nonexistent_music_id not found')

    @patch('flask_caching.Cache.delete')
    @patch('api.v1.views.playlist.invalidate_all_playlists_cache')
    def test_remove_music_from_playlist(self, mock_cache_invalidate, mock_cache_delete):
        """Test removing music from playlist"""
        self.login_user()
        # First add music to playlist
        self.client.post(
            f'/playlists/{self.test_playlist_id}',
            data={
                'action': 'add_music',
                'musicIds': [self.test_music_id]
            }
        )
        
        # Then remove it
        data = {
            'action': 'remove_music',
            'musicIds': [self.test_music_id]
        }
        
        response = self.client.post(
            f'/playlists/{self.test_playlist_id}',
            data=data
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['message'], 'Music removed from playlist successfully')
        self.assertIn('_links', response_data)

        # Verify cache invalidation calls
        mock_cache_invalidate.assert_called()
        mock_cache_delete.assert_any_call(f"playlist_{self.test_playlist_id}")
        mock_cache_delete.assert_any_call(f"playlist_{self.test_playlist_id}_user_{self.test_user_id}")

    @patch('flask_caching.Cache.get')
    @patch('flask_caching.Cache.set')
    def test_list_playlists(self, mock_cache_set, mock_cache_get):
        """Test listing all playlists"""
        mock_cache_get.return_value = None
        response = self.client.get('/playlists')

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('playlists', response_data)
        self.assertIn('total_count', response_data)
        self.assertIn('page', response_data)
        self.assertIn('limit', response_data)
        self.assertIn('_links', response_data)

        # Verify cache interactions
        mock_cache_get.assert_called_once()
        mock_cache_set.assert_called_once()

    @patch('flask_caching.Cache.delete')
    @patch('api.v1.views.playlist.invalidate_all_playlists_cache')
    def test_delete_playlist(self, mock_cache_invalidate, mock_cache_delete):
        """Test deleting a playlist"""
        self.login_user()
        response = self.client.delete(f'/playlists/{self.test_playlist_1_id}')

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['message'], 'Playlist deleted successfully')
        self.assertIn('_links', response_data)

        # Verify cache invalidation calls
        mock_cache_invalidate.assert_called()
        mock_cache_delete.assert_any_call(f"playlist_{self.test_playlist_1_id}")
        mock_cache_delete.assert_any_call(f"playlist_{self.test_playlist_1_id}_user_{self.test_user_id}")

    def test_delete_playlist_not_found(self):
        """Test deleting non-existent playlist"""
        self.login_user()
        response = self.client.delete('/playlists/nonexistent_id')

        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Playlist not found')

    def test_delete_playlist_unauthorized(self):
        """Test deleting playlist by non-owner"""
        
        # Login as different user
        with self.client.session_transaction() as session:
            session['user_id'] = self.other_user.id
            session['logged_in'] = True

        response = self.client.delete(f'/playlists/{self.test_playlist_id}')

        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Unauthorized to delete this playlist')
