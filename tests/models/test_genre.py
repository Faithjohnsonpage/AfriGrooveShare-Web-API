#!/usr/bin/env python3
import unittest
from datetime import datetime
from models import storage
from models.genre import Genre


class TestGenreDatabase(unittest.TestCase):

    def setUp(self):
        """Set up a test database and create genre instances."""
        # Create a genre instance
        self.genre = Genre()
        self.genre.name = "Pop"
        self.genre.save()

    def tearDown(self):
        """Tear down the test database by removing all entries."""
        genre = storage.get(Genre, self.genre.id)
        if genre:
            genre.delete()
            storage.save()

    def test_initialization(self):
        """Test initialization of Genre Model."""
        self.assertIsNotNone(self.genre.id)
        self.assertIsInstance(self.genre.created_at, datetime)
        self.assertIsInstance(self.genre.updated_at, datetime)

    def test_genre_creation(self):
        """Test that the genre instance is correctly saved in the database."""
        retrieved_genre = storage.get(Genre, self.genre.id)
        self.assertIsNotNone(retrieved_genre)
        self.assertEqual(retrieved_genre.name, "Pop")

    def test_genre_deletion(self):
        """Test that the genre instance is correctly deleted from the database."""
        saved_genre = storage.get(Genre, self.genre.id)
        saved_genre.delete()
        storage.save()
        deleted_genre = storage.get(Genre, self.genre.id)
        self.assertIsNone(deleted_genre)


if __name__ == "__main__":
    unittest.main()
