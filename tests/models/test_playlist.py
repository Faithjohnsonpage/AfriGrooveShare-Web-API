#!/usr/bin/env python3
import unittest
from datetime import datetime
from models import storage
from models.playlist import Playlist
from models.music import Music
from models.user import User
from models.artist import Artist
from models.genre import Genre
from models.album import Album


class TestPlaylistDatabase(unittest.TestCase):

    def setUp(self):
        """Set up a test database and create instances for Playlist testing."""
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
        self.album.save()

        # Create a genre instance
        self.genre = Genre()
        self.genre.name = "Pop"
        self.genre.save()

        # Create a music instance
        self.music = Music()
        self.music.title = "Bohemian Rhapsody"
        self.music.artist_id = self.artist.id
        self.music.album_id = self.album.id
        self.music.genre_id = self.genre.id
        self.music.file_url = "https://example.com/music/bohemian_rhapsody.mp3"
        self.music.duration = 354
        self.music.release_date = "1975-10-31"
        self.music.save()

        # Create a playlist instance
        self.playlist = Playlist()
        self.playlist.name = "My Rock Playlist"
        self.playlist.description = "Best rock songs"
        self.playlist.user_id = self.user.id
        self.playlist.save()

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
        self.assertIsNotNone(self.playlist.id)
        self.assertIsInstance(self.playlist.created_at, datetime)
        self.assertIsInstance(self.playlist.updated_at, datetime)

    def test_playlist_creation(self):
        """Test playlist creation and ensure it is saved to the database."""
        retrieved_playlist = storage.get(Playlist, self.playlist.id)
        self.assertIsNotNone(retrieved_playlist)
        self.assertEqual(retrieved_playlist.name, "My Rock Playlist")
        self.assertEqual(retrieved_playlist.description, "Best rock songs")
        self.assertEqual(retrieved_playlist.user_id, self.user.id)

    def test_add_music_to_playlist(self):
        """Test adding a music instance to the playlist."""
        self.playlist.add_music(Playlist, self.playlist.id, self.music)

        # Fetch the playlist from the database and check if the music was added
        updated_playlist = storage.get(Playlist, self.playlist.id)
        self.assertIn(self.music, updated_playlist.music)

    def test_remove_music_from_playlist(self):
        """Test removing a music instance from the playlist."""
        # First add the music to the playlist
        self.playlist.add_music(Playlist, self.playlist.id, self.music)

        # Now remove the music from the playlist
        self.playlist.remove_music(Playlist, self.playlist.id, self.music)

        # Fetch the playlist from the database and check if the music was removed
        updated_playlist = storage.get(Playlist, self.playlist.id)
        self.assertNotIn(self.music, updated_playlist.music)

    def test_playlist_deletion(self):
        """Test that the Playlist instance is correctly deleted from the database."""
        saved_playlist = storage.get(Playlist, self.playlist.id)
        self.assertIsNotNone(saved_playlist)

        # Now delete it and verify that it's gone
        saved_playlist.delete()
        storage.save()

        deleted_playlist = storage.get(Playlist, self.playlist.id)
        self.assertIsNone(deleted_playlist)


if __name__ == "__main__":
    unittest.main()
