#!/usr/bin/env python3
import unittest
import os
from models.user import User
from models.artist import Artist
from models.album import Album
from models.genre import Genre
from models.music import Music, ReleaseType
from models.news import News
from models.admin import Admin
from models import storage
from sqlalchemy.sql import text
from ..test_base_app import BaseTestCase
from unittest.mock import patch, Mock
from flask_caching import Cache
from flask import session, json
from datetime import datetime


class TestAdminAPI(BaseTestCase):
    """Test cases for Admin API endpoints"""

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

        # Create delete user
        cls.delete_user = User()
        cls.delete_user.username = "delete_user"
        cls.delete_user.email = "delete_user@example.com"
        cls.delete_user.password = "password456"
        cls.delete_user.save()

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

        # Create another artist instance with different values
        cls.new_artist = Artist()
        cls.new_artist.name = "Another Artist"
        cls.new_artist.bio = "An inspiring artist known for their impactful music."
        cls.new_artist.profile_picture_url = "http://example.com/another_artist.jpg"
        cls.new_artist.user_id = cls.user.id
        cls.new_artist.save()
        cls.new_test_artist_id = cls.new_artist.id

        # Create a genre instance
        cls.genre = Genre()
        cls.genre.name = "Pop"
        cls.genre.save()

        # Create a genre instance
        cls.new_genre = Genre()
        cls.new_genre.name = "LifeLine"
        cls.new_genre.save()

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

        # Create another music instance
        cls.new_music = Music()
        cls.new_music.title = "Imagine"
        cls.new_music.artist_id = cls.new_artist.id
        cls.new_music.genre_id = cls.genre.id
        cls.new_music.file_url = "https://example.com/music/imagine.mp3"
        cls.new_music.duration = 183
        cls.new_music.release_date = datetime.strptime("1971-10-11", "%Y-%m-%d").date()
        cls.new_music.cover_image_url = "http://example.com/music/imagine_cover.jpg"
        cls.new_music.description = "A classic song with a powerful message of peace."
        cls.new_music.release_type = ReleaseType.SINGLE
        cls.new_music.save()
        cls.new_test_music_id = cls.new_music.id


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

        # Create an admin instance
        cls.admin = Admin()
        cls.admin.user_id = cls.user.id
        cls.admin.save()

    @classmethod
    def tearDownClass(cls):
        """Teardown class-level resources"""

        users_to_delete = [
            'session@example.com',
            'other@example.com',
            'delete_user@example.com'
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
        rashbeats_genre = storage.filter_by(Genre, name='RashBeats')
        if rashbeats_genre:
            storage.delete(rashbeats_genre)
            storage.save()

    def login_user(self):
        """Helper method to log in the user and set up session"""
        with self.client.session_transaction() as session:
            session['user_id'] = self.test_user_id
            session['logged_in'] = True

    def test_get_all_users(self):
        """Test retrieving all users"""
        self.login_user()
        response = self.client.get('/admin/users')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertIn('users', data)
        self.assertIn('total_count', data)
        self.assertIn('_links', data)

    def test_get_all_users_unauthorized(self):
        """Test getting all users without authentication"""
        response = self.client.get('/admin/users')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data.decode())
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Unauthorized')

    def test_get_all_users_non_admin(self):
        """Test getting all users with non-admin user"""
        with self.client.session_transaction() as session:
            session['user_id'] = self.other_user.id
            session['logged_in'] = True

        response = self.client.get('/admin/users')
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode())
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Admin privileges required')
 
    def test_get_all_users_with_pagination(self):
        """Test users retrieval with pagination parameters"""
        self.login_user()

        response = self.client.get('/admin/users?page=2&limit=1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())

        self.assertEqual(len(data['users']), 1)
        self.assertIn('prev', data['_links'])
        self.assertTrue(data['_links']['prev'] is not None)

    def test_delete_user_unauthorized(self):
        """Test deleting user without authentication"""
        response = self.client.delete(f'/admin/users/{self.delete_user.id}')
        self.assertEqual(response.status_code, 401)

    def test_delete_user_non_admin(self):
        """Test deleting user with non-admin user"""
        with self.client.session_transaction() as session:
            session['user_id'] = self.other_user.id
            session['logged_in'] = True

        response = self.client.delete(f'/admin/users/{self.test_user_id}')
        self.assertEqual(response.status_code, 403)

    def test_delete_user_not_found(self):
        """Test deleting non-existent user"""
        self.login_user()
        response = self.client.delete('/admin/users/nonexistent_id')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data.decode())
        self.assertEqual(data['error'], 'User not found')

    def test_delete_user_success(self):
        """Test successfully deleting a user"""
        self.login_user()
        response = self.client.delete(f'/admin/users/{self.delete_user.id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['message'], 'User deleted successfully')
        self.assertIn('_links', data)

    def test_delete_artist_unauthorized(self):
        """Test deleting artist without authentication"""
        response = self.client.delete(f'/admin/artists/{self.test_artist_id}')
        self.assertEqual(response.status_code, 401)

    def test_delete_artist_not_found(self):
        """Test deleting non-existent artist"""
        self.login_user()
        response = self.client.delete('/admin/artists/nonexistent_id')
        self.assertEqual(response.status_code, 404)

    def test_delete_artist_success(self):
        """Test successfully deleting an artist"""
        self.login_user()
        response = self.client.delete(f'/admin/artists/{self.test_artist_id}')
        self.assertEqual(response.status_code, 200)

    def test_delete_album_unauthorized(self):
        """Test deleting album without authentication"""
        response = self.client.delete(f'/admin/albums/{self.test_album_id}')
        self.assertEqual(response.status_code, 401)

    def test_delete_album_not_found(self):
        """Test deleting non-existent album"""
        self.login_user()
        response = self.client.delete('/admin/albums/nonexistent_id')
        self.assertEqual(response.status_code, 404)

    def test_delete_album_success(self):
        """Test successfully deleting an album"""
        self.login_user()
        response = self.client.delete(f'/admin/albums/{self.test_album_id}')
        self.assertEqual(response.status_code, 200)

    def test_get_all_admins_unauthorized(self):
        """Test getting all admins without authentication"""
        response = self.client.get('/admin/list')
        self.assertEqual(response.status_code, 401)

    def test_get_all_admins_success(self):
        """Test successfully retrieving all admins"""
        self.login_user()

        response = self.client.get('/admin/list')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())

        self.assertIn('admins', data)
        self.assertIn('total_count', data)
        self.assertIn('_links', data)

    def test_delete_single_unauthorized(self):
        """Test deleting single music without authentication"""
        response = self.client.delete(f'/admin/music/{self.test_music_id}')
        self.assertEqual(response.status_code, 401)

    def test_delete_single_not_found(self):
        """Test deleting non-existent music"""
        self.login_user()
        response = self.client.delete('/admin/music/nonexistent_id')
        self.assertEqual(response.status_code, 404)

    def test_delete_album_track(self):
        """Test attempting to delete an album track"""
        self.login_user()
        response = self.client.delete(f'/admin/music/{self.test_album_music_id}')
        self.assertEqual(response.status_code, 403)

    def test_delete_single_success(self):
        """Test successfully deleting a single track"""
        self.login_user()
        response = self.client.delete(f'/admin/music/{self.new_test_music_id}')
        self.assertEqual(response.status_code, 200)

    def test_delete_news_unauthorized(self):
        """Test deleting news without authentication"""
        response = self.client.delete(f'/admin/news/{self.test_news1_id}')
        self.assertEqual(response.status_code, 401)

    def test_delete_news_not_found(self):
        """Test deleting non-existent news"""
        self.login_user()
        response = self.client.delete('/admin/news/nonexistent_id')
        self.assertEqual(response.status_code, 404)

    def test_delete_news_success(self):
        """Test successfully deleting a news article"""
        self.login_user()
        response = self.client.delete(f'/admin/news/{self.test_news1_id}')
        self.assertEqual(response.status_code, 200)

    def test_get_news_for_review_unauthorized(self):
        """Test getting news for review without authentication"""
        response = self.client.get('/admin/news/review')
        self.assertEqual(response.status_code, 401)

    def test_get_news_for_review_success(self):
        """Test successfully retrieving news for review"""
        self.login_user()
        
        response = self.client.get('/admin/news/review')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        
        self.assertIn('pending_news', data)
        self.assertIn('total', data)
        self.assertIn('_links', data)

    def test_review_news_unauthorized(self):
        """Test reviewing news without authentication"""
        response = self.client.post(f'/admin/news/{self.test_news1_id}/review')
        self.assertEqual(response.status_code, 401)

    def test_review_news_not_found(self):
        """Test reviewing non-existent news"""
        self.login_user()
        response = self.client.post('/admin/news/nonexistent_id/review', 
                                   json={'action': 'approve'})
        self.assertEqual(response.status_code, 404)

    def test_review_news_invalid_action(self):
        """Test reviewing news with invalid action"""
        self.login_user()
        response = self.client.post(f'/admin/news/{self.test_news2_id}/review',
                                   json={'action': 'invalid'})
        self.assertEqual(response.status_code, 400)

    def test_review_news_success_approve(self):
        """Test successfully approving news"""
        self.login_user()
        response = self.client.post(f'/admin/news/{self.test_news2_id}/review',
                                   json={'action': 'approve'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['message'], 'News post approved successfully')

    def test_review_news_success_reject(self):
        """Test successfully rejecting news"""
        self.login_user()
        response = self.client.post(f'/admin/news/{self.test_news2_id}/review',
                                   json={'action': 'reject'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['message'], 'News post rejected successfully')

    def test_add_genre_unauthorized(self):
        """Test adding genre without authentication"""
        response = self.client.post('/admin/genres', json={'name': 'Rock'})
        self.assertEqual(response.status_code, 401)

    def test_add_genre_missing_name(self):
        """Test adding genre without name"""
        self.login_user()
        response = self.client.post('/admin/genres', json={})
        self.assertEqual(response.status_code, 400)

    def test_add_genre_duplicate(self):
        """Test adding duplicate genre"""
        self.login_user()
        response = self.client.post('/admin/genres', json={'name': 'Pop'})
        self.assertEqual(response.status_code, 400)

    def test_add_genre_success(self):
        """Test successfully adding a genre"""
        self.login_user()
        response = self.client.post('/admin/genres', json={'name': 'RashBeats'})
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode())
        self.assertIn('id', data)
        self.assertIn('_links', data)

    def test_update_genre_unauthorized(self):
        """Test updating genre without authentication"""
        response = self.client.put(f'/admin/genres/{self.genre.id}', 
                                  json={'name': 'New Pop'})
        self.assertEqual(response.status_code, 401)

    def test_update_genre_not_found(self):
        """Test updating non-existent genre"""
        self.login_user()
        response = self.client.put('/admin/genres/nonexistent_id',
                                  json={'name': 'New Pop'})
        self.assertEqual(response.status_code, 404)

    def test_update_genre_missing_name(self):
        """Test updating genre without name"""
        self.login_user()
        response = self.client.put(f'/admin/genres/{self.genre.id}', json={})
        self.assertEqual(response.status_code, 400)

    def test_update_genre_success(self):
        """Test successfully updating a genre"""
        self.login_user()
        response = self.client.put(f'/admin/genres/{self.genre.id}',
                                  json={'name': 'New Pop'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['message'], 'Genre updated successfully')

    def test_delete_genre_unauthorized(self):
        """Test deleting genre without authentication"""
        response = self.client.delete(f'/admin/genres/{self.genre.id}')
        self.assertEqual(response.status_code, 401)

    def test_delete_genre_not_found(self):
        """Test deleting non-existent genre"""
        self.login_user()
        response = self.client.delete('/admin/genres/nonexistent_id')
        self.assertEqual(response.status_code, 404)

    def test_delete_genre_success(self):
        """Test successfully deleting a genre"""
        self.login_user()
        response = self.client.delete(f'/admin/genres/{self.new_genre.id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['message'], 'Genre deleted successfully') 
