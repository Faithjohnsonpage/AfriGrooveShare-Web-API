#!/usr/bin/env python3
import unittest
from datetime import datetime
from models import storage
from models.news import News
from models.user import User


class TestNewsDatabase(unittest.TestCase):

    def setUp(self):
        """Set up a test database and create a user and news instance."""
        # Create a user instance
        self.user = User()
        self.user.username = "test_user"
        self.user.email = "test@example.com"
        self.user.password = "securepassword"
        self.user.profile_picture_url = "http://example.com/profile.jpg"
        self.user.reset_token = "reset_token_value"
        self.user.save()

        # Create a news instance
        self.news = News()
        self.news.title = "Test News"
        self.news.content = "This is a test news content."
        self.news.author = "John Doe"
        self.news.category = "Music Technology"
        self.news.user_id = self.user.id
        self.news.save()

    def tearDown(self):
        """Tear down the test database by removing all entries."""
        user = storage.get(User, self.user.id)
        if user:
            user.delete()
            storage.save()

    def test_initialization(self):
        """Test initialization of News Model."""
        self.assertIsNotNone(self.news.id)
        self.assertIsInstance(self.news.created_at, datetime)
        self.assertIsInstance(self.news.updated_at, datetime)

    def test_news_creation(self):
        """Test that the news instance is correctly saved in the database."""
        # Verify that the object is saved in the database
        retrieved_news = storage.get(News, self.news.id)
        self.assertIsNotNone(retrieved_news)
        self.assertEqual(retrieved_news.title, "Test News")
        self.assertEqual(retrieved_news.user_id, self.user.id)
        self.assertEqual(retrieved_news.author, "John Doe")
        self.assertEqual(retrieved_news.category, "Music Technology")
        self.assertEqual(retrieved_news.status, 'live')
        self.assertFalse(retrieved_news.reviewed)

    def test_news_update_status(self):
        """Test updating the status and reviewed fields."""
        # Verify initial status and reviewed state
        retrieved_news = storage.get(News, self.news.id)
        self.assertEqual(retrieved_news.status, 'live')
        self.assertFalse(retrieved_news.reviewed)

        # Update the news to be 'private' and reviewed
        retrieved_news.status = 'private'
        retrieved_news.reviewed = True
        retrieved_news.save()

        # Verify that the news has been updated
        updated_news = storage.get(News, self.news.id)
        self.assertEqual(updated_news.status, 'private')
        self.assertTrue(updated_news.reviewed)

    def test_news_deletion(self):
        """Test that the news instance is correctly deleted from the database."""
        # Verify that the news exists in the database
        saved_news = storage.get(News, self.news.id)
        self.assertIsNotNone(saved_news)

        # Now delete it and verify that it's gone
        saved_news.delete()
        storage.save()

        deleted_news = storage.get(News, self.news.id)
        self.assertIsNone(deleted_news)


if __name__ == "__main__":
    unittest.main()
