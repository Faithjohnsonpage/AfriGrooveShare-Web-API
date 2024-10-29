#!/usr/bin/env python3
import unittest
from models import storage
from models.genre import Genre
from ..test_base_app import BaseTestCase


class GenreListTestCase(BaseTestCase):
    
    def test_predefined_genres_listed(self):
        """Test that predefined genres are returned in the /genres endpoint"""
        response = self.client.get('/genres')
        data = response.get_json()
        
        # Check response status code
        self.assertEqual(response.status_code, 200)
        
        # Check that each predefined genre is in the response
        predefined_genres = ["Pop", "Rock", "Jazz", "Classical", 
                             "Hip-Hop", "Gospel", "Electronic", "Reggae", "Blues"]
                             
        genre_names = {genre['name'] for genre in data}
        for genre in predefined_genres:
            self.assertIn(genre, genre_names)
