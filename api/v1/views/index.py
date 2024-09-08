#!/usr/bin/env python3
from flask import jsonify
from api.v1.views import app_views
from models import storage
from models.user import User
from models.music import Music
from models.playlist import Playlist
from models.news import News
from models.album import Album
from models.artist import Artist


@app_views.route('/status', methods=['GET'], strict_slashes=False)
def status():
    """Returns the status of the API"""
    return jsonify({"status": "OK"}), 200


@app_views.route('/stats', methods=['GET'], strict_slashes=False)
def stats():
    """Returns the number of each object in the database"""
    stats = {
        "users": storage.count(User),
        "artists": storage.count(Artist),
        "albums": storage.count(Album),
        "music": storage.count(Music),
        "playlists": storage.count(Playlist),
        "news": storage.count(News)
    }
    return jsonify(stats), 200
