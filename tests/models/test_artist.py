#!/usr/bin/env python3
import unittest
from datetime import datetime
from models import storage
from models.artist import Artist
from models.user import User

class TestArtistDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the test database and create user and artist instances for all tests."""
        # Create a user instance
        cls.user = User()
        cls.user.username = "test_user"
        cls.user.email = "test@example.com"
        cls.user.password = "securepassword"
        cls.user.profile_picture_url = "http://example.com/profile.jpg"
        cls.user.reset_token = "reset_token_value"
        cls.user.save()

        # Create an artist instance
        cls.artist = Artist()
        cls.artist.name = "Test Artist"
        cls.artist.bio = "This is a test artist bio."
        cls.artist.profile_picture_url = "http://example.com/artist.jpg"
        cls.artist.user_id = cls.user.id
        cls.artist.save()

    @classmethod
    def tearDownClass(cls):
        """Tear down the test database by removing all entries once after all tests."""
        user = storage.get(User, cls.user.id)
        if user:
            user.delete()
            storage.save()

    def test_initialization(self):
        """Test initialization of Artist Model."""
        self.assertIsNotNone(self.artist.id)
        self.assertIsInstance(self.artist.created_at, datetime)
        self.assertIsInstance(self.artist.updated_at, datetime)

    def test_artist_creation(self):
        """Test that the artist instance is correctly saved in the database."""
        retrieved_artist = storage.get(Artist, self.artist.id)
        self.assertIsNotNone(retrieved_artist)
        self.assertEqual(retrieved_artist.name, "Test Artist")
        self.assertEqual(retrieved_artist.bio, "This is a test artist bio.")
        self.assertEqual(retrieved_artist.profile_picture_url, "http://example.com/artist.jpg")
        self.assertEqual(retrieved_artist.user_id, self.user.id)

    def test_artist_deletion(self):
        """Test that the artist instance is correctly deleted from the database."""
        saved_artist = storage.get(Artist, self.artist.id)
        saved_artist.delete()
        storage.save()
        deleted_artist = storage.get(Artist, self.artist.id)
        self.assertIsNone(deleted_artist)


if __name__ == "__main__":
    unittest.main()
