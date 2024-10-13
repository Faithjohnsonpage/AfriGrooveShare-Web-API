#!/usr/bin/env python3
import unittest
from models import storage
from models.user import User
from models.artist import Artist

class TestDBEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the test DB and initialize storage"""
        # Create a user instance
        cls.user = User()
        cls.user.username = "test_user"
        cls.user.email = "test@example.com"
        cls.user.password = "securepassword"
        cls.user.profile_picture_url = "http://example.com/profile.jpg"
        cls.user.reset_token = "reset_token_value"
        cls.user.save()

    @classmethod
    def tearDownClass(cls):
        """Tear down by deleting the user after all tests"""
        user = storage.get(User, cls.user.id)
        if user:
            storage.delete(user)
            storage.save()

    def test_new(self):
        """Test adding a new user object to the session"""
        self.assertIsNotNone(storage.get(User, self.user.id))

    def test_save(self):
        """Test saving user objects to the database"""
        # Create an artist instance
        self.artist = Artist()
        self.artist.name = "Test Artist"
        self.artist.bio = "This is a test artist bio."
        self.artist.profile_picture_url = "http://example.com/artist.jpg"
        self.artist.user_id = self.user.id
        self.artist.save()

        artist = storage.get(User, self.user.id)
        self.assertIsNotNone(artist)
    
    def test_get(self):
        """Test retrieving a user by primary key"""
        retrieved_user = storage.get(User, self.user.id)
        self.assertEqual(retrieved_user.username, "test_user")

    def test_all(self):
        """Test retrieving all users"""
        all_users = storage.all(User)
        self.assertGreaterEqual(len(all_users), 1)

    def test_filter_by(self):
        """Test filtering users based on specific criteria"""
        filtered_users = storage.filter_by(User, username="test_user")
        self.assertEqual(filtered_users.email, "test@example.com")

    def test_count(self):
        """Test counting the number of user objects"""
        user_count = storage.count(User)
        self.assertGreaterEqual(user_count, 1)

    def test_exists(self):
        """Test checking if a user object exists"""
        exists = storage.exists(User, username="test_user")
        self.assertTrue(exists)

    def test_reload(self):
        """Test reloading the storage session"""
        storage.reload()
        session = storage.get_engine().connect()
        self.assertIsNotNone(session)

    
if __name__ == "__main__":
    unittest.main()

