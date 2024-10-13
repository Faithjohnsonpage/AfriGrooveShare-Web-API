#!/usr/bin/env python3
import unittest
from unittest.mock import patch
from datetime import datetime
from models.base_model import BaseModel


class TestBaseModel(unittest.TestCase):
    def setUp(self):
        """Set up for each test."""
        # Create an instance of BaseModel for testing
        self.base_model = BaseModel()

    def tearDown(self):
        """Tear down for each test."""
        pass

    def test_initialization(self):
        """Test initialization of BaseModel."""
        self.assertIsNotNone(self.base_model.id)
        self.assertIsInstance(self.base_model.created_at, datetime)
        self.assertIsInstance(self.base_model.updated_at, datetime)

    @patch('models.storage.new')
    @patch('models.storage.save')
    def test_save(self, mock_save, mock_new):
        """Test saving BaseModel to storage."""
        self.base_model.save()

        # Verify that storage.new and storage.save were called
        mock_new.assert_called_with(self.base_model)
        mock_save.assert_called_once()

    @patch('models.storage')
    def test_delete(self, mock_storage):
        """Test deleting BaseModel from storage."""

        def mock_delete(instance):
            # Simulate deletion by setting instance to None
            instance = None
            return instance

        mock_storage.delete.side_effect = mock_delete
        self.base_model.delete()
        mock_storage.delete.assert_called_once_with(self.base_model)
        self.assertIsNone(mock_storage.delete(self.base_model))

    def test_str(self):
        """Test __str__ method of BaseModel."""
        expected_str = f"[{self.base_model.__class__.__name__}] "\
                       f"({self.base_model.id}) {self.base_model.__dict__}"
        self.assertEqual(str(self.base_model), expected_str)

    def test_to_dict(self):
        """Test to_dict method of BaseModel."""
        base_dict = self.base_model.to_dict()
        self.assertEqual(base_dict["__class__"], self.base_model.__class__.__name__)
        self.assertEqual(base_dict["id"], self.base_model.id)
        self.assertEqual(base_dict["created_at"], self.base_model.created_at.strftime("%Y-%m-%dT%H:%M:%S.%f"))
        self.assertEqual(base_dict["updated_at"], self.base_model.updated_at.strftime("%Y-%m-%dT%H:%M:%S.%f"))


if __name__ == '__main__':
    unittest.main()
