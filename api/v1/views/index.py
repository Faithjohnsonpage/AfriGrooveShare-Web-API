#!/usr/bin/env python3
from flask import jsonify, current_app
from api.v1.views import app_views
from models import storage
from models.user import User
from models.music import Music
from models.playlist import Playlist
from models.news import News
from models.album import Album
from models.artist import Artist
from functools import wraps


def get_limiter():
    """Safely get limiter from current_app"""
    try:
        return current_app.limiter
    except Exception:
        return None


def custom_limit(limit_string):
    """Decorator for custom rate limiting"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            limiter = get_limiter()
            if limiter:
                decorated = limiter.limit(limit_string)(f)
                return decorated(*args, **kwargs)
            return f(*args, **kwargs)
        return wrapped
    return decorator


@app_views.route('/status', methods=['GET'], strict_slashes=False)
@custom_limit("1 per day")
def status():
    """Returns the status of the API"""
    return jsonify({"status": "OK"}), 200


@app_views.route('/stats', methods=['GET'], strict_slashes=False)
@custom_limit("1 per day")
def stats():
    """Returns the number of each object in the database"""
    try:
        stats = {
            "users": storage.count(User),
            "artists": storage.count(Artist),
            "albums": storage.count(Album),
            "music": storage.count(Music),
            "playlists": storage.count(Playlist),
            "news": storage.count(News)
        }
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": "Failed to retrieve stats"}), 500
