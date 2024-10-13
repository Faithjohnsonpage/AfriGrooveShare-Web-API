#!/usr/bin/env python3
import unittest
from datetime import datetime
from models import storage
from models.album import Album
from models.artist import Artist
from models.user import User


class TestAlbumDatabase(unittest.TestCase):

    def setUp(self):
        """Set up a test database and create an artist and album instance."""
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

    def tearDown(self):
        """Tear down the test database by removing all entries."""
        user = storage.get(User, self.user.id)
        if user:
            user.delete()
            storage.save()

    def test_initialization(self):
        """Test initialization of Album Model."""
        self.assertIsNotNone(self.album.id)
        self.assertIsInstance(self.album.created_at, datetime)
        self.assertIsInstance(self.album.updated_at, datetime)

    def test_album_creation(self):
        """Test that the album instance is correctly saved in the database."""
        # Verify that the object is saved in the database
        retrieved_album = storage.get(Album, self.album.id)
        self.assertIsNotNone(retrieved_album)
        self.assertEqual(retrieved_album.title, "Test Album")
        self.assertEqual(retrieved_album.artist_id, self.artist.id)
        self.assertEqual(retrieved_album.release_date, "2024-01-01")
        self.assertEqual(retrieved_album.cover_image_url, "http://example.com/image.jpg")
        self.assertEqual(retrieved_album.description, "This is a test album description.")

    def test_album_deletion(self):
        """Test that the album instance is correctly deleted from the database."""
        # Verify that the album exists in the database
        saved_album = storage.get(Album, self.album.id)
        self.assertIsNotNone(saved_album)

        # Now delete it and verify that it's gone
        saved_album.delete()
        storage.save()

        deleted_album = storage.get(Album, self.album.id)
        self.assertIsNone(deleted_album)


if __name__ == "__main__":
    unittest.main()
