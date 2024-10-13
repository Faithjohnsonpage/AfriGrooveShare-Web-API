#!/usr/bin/env python3
import unittest
from models import storage
from models.admin import Admin
from models.user import User
from datetime import datetime


class TestAdminDatabase(unittest.TestCase):

    def setUp(self):
        """Set up a test database and create a user instance for the admin."""
        # Create a user instance
        self.user = User()
        self.user.username = "admin_user"
        self.user.email = "admin@example.com"
        self.user.password = "securepassword"
        self.user.profile_picture_url = "http://example.com/admin_profile.jpg"
        self.user.reset_token = "reset_token_value"
        self.user.save()

        # Create an admin instance
        self.admin = Admin()
        self.admin.user_id = self.user.id
        self.admin.save()

    def tearDown(self):
        """Tear down the test database by removing all entries."""
        user = storage.get(User, self.user.id)
        if user:
            user.delete()
        storage.save()

    def test_admin_initialization(self):
        """Test initialization of Admin model."""
        self.assertIsNotNone(self.admin.id)
        self.assertEqual(self.admin.user_id, self.user.id)
        self.assertIsInstance(self.admin.created_at, datetime)
        self.assertIsInstance(self.admin.updated_at, datetime)

    def test_admin_association_with_user(self):
        """Test that the admin is correctly associated with a user."""
        retrieved_admin = storage.get(Admin, self.admin.id)
        self.assertIsNotNone(retrieved_admin)
        self.assertEqual(retrieved_admin.user_id, self.user.id)

        # Verify the user associated with the admin
        associated_user = storage.get(User, retrieved_admin.user_id)
        self.assertIsNotNone(associated_user)
        self.assertEqual(associated_user.username, "admin_user")
        self.assertEqual(associated_user.email, "admin@example.com")

    def test_admin_deletion(self):
        """Test that an admin instance can be deleted and its user remains."""
        # Ensure the admin exists in the database
        admin = storage.get(Admin, self.admin.id)
        self.assertIsNotNone(admin)

        # Delete the admin instance
        admin.delete()
        storage.save()

        deleted_admin = storage.get(Admin, self.admin.id)
        self.assertIsNone(deleted_admin)

        # Verify that the associated user still exists
        user = storage.get(User, self.user.id)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "admin_user")


if __name__ == "__main__":
    unittest.main()
