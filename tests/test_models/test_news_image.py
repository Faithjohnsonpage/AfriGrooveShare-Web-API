#!/usr/bin/env python3
import unittest
from models import storage
from models.news import News
from models.news_image import NewsImage
from models.user import User


class TestNewsImageDatabase(unittest.TestCase):

    def setUp(self):
        """Set up a test database and create a user, news, and news image instance."""
        # Create a user instance
        self.user = User()
        self.user.username = "test_user"
        self.user.email = "test@example.com"
        self.user.password = "securepassword"
        self.user.profile_picture_url = "http://example.com/profile.jpg"
        self.user.save()

        # Create a news instance
        self.news = News()
        self.news.title = "Test News"
        self.news.content = "This is a test news content."
        self.news.author = "John Doe"
        self.news.category = "Music Technology"
        self.news.user_id = self.user.id
        self.news.save()

        # Create a news image instance
        self.news_image = NewsImage()
        self.news_image.news_id = self.news.id
        self.news_image.image_url = "http://example.com/news_image.jpg"
        self.news_image.save()

    def tearDown(self):
        """Tear down the test database by removing all entries."""
        user = storage.get(User, self.user.id)
        if user:
            user.delete()
            storage.save()

    def test_news_image_creation(self):
        """Test that the NewsImage instance is correctly saved in the database."""
        # Verify that the news image is saved in the database
        retrieved_image = storage.get(NewsImage, self.news_image.id)
        self.assertIsNotNone(retrieved_image)
        self.assertEqual(retrieved_image.news_id, self.news.id)
        self.assertEqual(retrieved_image.image_url, "http://example.com/news_image.jpg")

    def test_news_image_deletion(self):
        """Test that deleting a news image"""
        # Verify that the news image exists in the database
        saved_image = storage.get(NewsImage, self.news_image.id)
        self.assertIsNotNone(saved_image)

        saved_image.delete()
        storage.save()
        deleted_image = storage.get(NewsImage, self.news_image.id)
        self.assertIsNone(deleted_image)

    def test_multiple_images_for_news(self):
        """Test adding multiple images for a single news entry."""
        # Create a second image for the same news
        second_image = NewsImage()
        second_image.news_id = self.news.id
        second_image.image_url = "http://example.com/second_image.jpg"
        second_image.save()

        # Retrieve both images and verify they are associated with the same news
        first_image = storage.get(NewsImage, self.news_image.id)
        second_image_retrieved = storage.get(NewsImage, second_image.id)
        self.assertEqual(first_image.news_id, self.news.id)
        self.assertEqual(second_image_retrieved.news_id, self.news.id)

        # Verify the URLs are correct
        self.assertEqual(first_image.image_url, "http://example.com/news_image.jpg")
        self.assertEqual(second_image_retrieved.image_url, "http://example.com/second_image.jpg")

    
if __name__ == "__main__":
    unittest.main()

