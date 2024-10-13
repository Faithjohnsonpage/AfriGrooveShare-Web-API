#!/usr/bin/env python3
import unittest
from datetime import datetime
from models import storage
from models.music import Music
from models.artist import Artist
from models.album import Album
from models.genre import Genre
from models.user import User
from models.music import ReleaseType


class TestMusicDatabase(unittest.TestCase):

    def setUp(self):
        """Set up a test database and create instances for Music testing."""
        # Create a user instance
        self.user = User()
        self.user.username = "test_user"
        self.user.email = "test@example.com"
        self.user.password = "securepassword"
        self.user.profile_picture_url = "http://example.com/profile.jpg"
        self.user.reset_token = "reset_token_value"
        self.user.save()

        # Create an artist instance
        self.artist = Artist()
        self.artist.name = "Test Artist"
        self.artist.bio = "This is a test artist bio."
        self.artist.profile_picture_url = "http://example.com/artist.jpg"
        self.artist.user_id = self.user.id
        self.artist.save()

        # Create an album instance
        self.album = Album()
        self.album.title = "Test Album"
        self.album.artist_id = self.artist.id
        self.album.release_date = "2024-01-01"
        self.album.cover_image_url = "http://example.com/image.jpg"
        self.album.description = "This is a test album description."
        self.album.save()

        # Create a genre instance
        self.genre = Genre()
        self.genre.name = "Pop"
        self.genre.save()

        # Create a music instance with the new fields
        self.music = Music()
        self.music.title = "Bohemian Rhapsody"
        self.music.artist_id = self.artist.id
        self.music.album_id = self.album.id
        self.music.genre_id = self.genre.id
        self.music.file_url = "https://example.com/music/bohemian_rhapsody.mp3"
        self.music.duration = 354
        self.music.release_date = "1975-10-31"
        self.music.cover_image_url = "http://example.com/music/bohemian_rhapsody_cover.jpg"
        self.music.description = "A test description for the music track."
        self.music.release_type = ReleaseType.SINGLE
        self.music.save()

    def tearDown(self):
        """Tear down the test database by removing all entries."""
        user = storage.get(User, self.user.id)
        if user:
            user.delete()
            storage.save()

        genre = storage.get(Genre, self.genre.id)
        if genre:
            genre.delete()
            storage.save()

    def test_initialization(self):
        """Test initialization of Music Model."""
        self.assertIsNotNone(self.music.id)
        self.assertIsInstance(self.music.created_at, datetime)
        self.assertIsInstance(self.music.updated_at, datetime)

    def test_music_creation(self):
        """Test that the Music instance is correctly saved in the database."""
        retrieved_music = storage.get(Music, self.music.id)
        self.assertIsNotNone(retrieved_music)
        self.assertEqual(retrieved_music.title, "Bohemian Rhapsody")
        self.assertEqual(retrieved_music.artist_id, self.artist.id)
        self.assertEqual(retrieved_music.album_id, self.album.id)
        self.assertEqual(retrieved_music.genre_id, self.genre.id)
        self.assertEqual(retrieved_music.file_url, "https://example.com/music/bohemian_rhapsody.mp3")
        self.assertEqual(retrieved_music.duration, 354)
        self.assertEqual(retrieved_music.cover_image_url, "http://example.com/music/bohemian_rhapsody_cover.jpg")
        self.assertEqual(retrieved_music.description, "A test description for the music track.")
        self.assertEqual(retrieved_music.release_type, ReleaseType.SINGLE)

    def test_music_deletion(self):
        """Test that the Music instance is correctly deleted from the database."""
        saved_music = storage.get(Music, self.music.id)
        self.assertIsNotNone(saved_music)

        # Now delete it and verify that it's gone
        saved_music.delete()
        storage.save()

        deleted_music = storage.get(Music, self.music.id)
        self.assertIsNone(deleted_music)


if __name__ == "__main__":
    unittest.main()
