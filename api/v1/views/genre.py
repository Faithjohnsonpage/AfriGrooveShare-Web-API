#!/usr/bin/env python3
from flask import jsonify, request
from models import storage
from models.genre import Genre
from api.v1.views import app_views


predefined_genres = ["Pop", "Rock", "Jazz", "Classical", 
                     "Hip-Hop", "Gospel", "Electronic", "Reggae", "Blues"]

for genre_name in predefined_genres:
    genre = Genre()
    genre.name = genre_name
    storage.new(genre)

storage.save()

@app_views.route('/genres', methods=['GET'], strict_slashes=False)
def list_genres():
    """List all predefined genres"""
    genres = storage.all(Genre)
    return jsonify([{"id": genre.id, "name": genre.name}
                    for genre in genres]), 200
