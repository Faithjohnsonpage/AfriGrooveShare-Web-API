#!/usr/bin/env python3
import unittest
from models import storage
from datetime import datetime
from models.user import User


class TestUserDatabase(unittest.TestCase):

    def setUp(self):
        """Set up a test database and create a user instance."""
        # Create a user instance
        self.user = User()
        self.user.username = "test_user"
        self.user.email = "test@example.com"
        self.user.password = "securepassword"
        self.user.profile_picture_url = "http://example.com/profile.jpg"
        self.user.reset_token = "reset_token_value"
        self.user.save()

    def tearDown(self):
        """Tear down the test database by removing all entries."""
        user = storage.get(User, self.user.id)
        if user:
            user.delete()
            storage.save()

    def test_initialization(self):
        """Test initialization of User Model."""
        self.assertIsNotNone(self.user.id)
        self.assertIsInstance(self.user.created_at, datetime)
        self.assertIsInstance(self.user.updated_at, datetime)

    def test_user_creation(self):
        """Test that the user instance is correctly saved in the database."""
        # Verify that the user is saved in the database
        retrieved_user = storage.get(User, self.user.id)
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.username, "test_user")
        self.assertEqual(retrieved_user.email, "test@example.com")
        self.assertTrue(retrieved_user.verify_password("securepassword"))
        self.assertEqual(retrieved_user.profile_picture_url, "http://example.com/profile.jpg")
        self.assertEqual(retrieved_user.reset_token, "reset_token_value")

    def test_user_password_hashing(self):
        """Test that the password is hashed correctly."""
        self.user.password = "newpassword"
        self.assertNotEqual(self.user.password_hash, "newpassword")
        self.assertTrue(self.user.verify_password("newpassword"))

    def test_user_deletion(self):
        """Test that the user instance is correctly deleted from the database."""
        # Verify that the user exists in the database
        saved_user = storage.get(User, self.user.id)
        self.assertIsNotNone(saved_user)

        # Now delete it and verify that it's gone
        saved_user.delete()
        storage.save()
        deleted_user = storage.get(User, self.user.id)
        self.assertIsNone(deleted_user)


if __name__ == "__main__":
    unittest.main()
