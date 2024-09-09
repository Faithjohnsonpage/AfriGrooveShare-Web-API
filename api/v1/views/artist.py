#!/usr/bin/env python3
from flask import jsonify, request, session
from models import storage
from models.artist import Artist
from api.v1.views import app_views
from werkzeug.utils import secure_filename
from PIL import Image
import os
import imghdr
import uuid


UPLOAD_FOLDER = 'api/v1/uploads/artist_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_CONTENT_LENGTH = 5 * 1000 * 1000


@app_views.route('/artists', methods=['POST'], strict_slashes=False)
def create_artist() -> str:
    """Create a new artist"""
    if 'user_id' not in session:
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    name = request.form.get('name')
    bio = request.form.get('bio')
    if not name:
        return jsonify({"error": "Missing name"}), 400

    artist = Artist()
    artist.name = name
    artist.bio = bio
    artist.user_id = user_id
    storage.new(artist)
    storage.save()

    return jsonify({"message": "Artist created successfully", "artistId": artist.id}), 201


@app_views.route('/artists/<string:artist_id>', methods=['GET'], strict_slashes=False)
def get_artist(artist_id: str) -> str:
    """Retrieve an artist by ID"""
    if 'user_id' not in session:
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    artist = storage.get(Artist, artist_id)
    if not artist:
        return jsonify({"error": "Artist not found"}), 404

    return jsonify({
        "artist": {
            "id": artist.id,
            "name": artist.name,
            "bio": artist.bio,
            "profile_picture_url": artist.profile_picture_url
        }
    }), 200


@app_views.route('/artists/<string:artist_id>', methods=['PUT'], strict_slashes=False)
def update_artist(artist_id: str) -> str:
    """Update an artist by ID"""
    if 'user_id' not in session:
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    artist = storage.get(Artist, artist_id)
    if not artist:
        return jsonify({"error": "Artist not found"}), 404

    name = request.form.get('name')
    bio = request.form.get('bio')
    if name:
        artist.name = name
    if bio:
        artist.bio = bio

    storage.save()
    return jsonify({"message": "Artist updated successfully"}), 200


@app_views.route('/artists/<string:artist_id>', methods=['DELETE'], strict_slashes=False)
def delete_artist(artist_id: str) -> str:
    """Delete an artist by ID"""
    if 'user_id' not in session:
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    artist = storage.get(Artist, artist_id)
    if not artist:
        return jsonify({"error": "Artist not found"}), 404

    storage.delete(artist)
    storage.save()
    return jsonify({"message": "Artist deleted successfully"}), 200


@app_views.route('/artists', methods=['GET'], strict_slashes=False)
def list_artists():
    """List all artists"""
    artists = storage.all(Artist)

    return jsonify({
        "artists": [
            {
                "id": artist.id,
                "name": artist.name,
                "profile_picture_url": artist.profile_picture_url
            } for artist in artists
        ]
    }), 200


@app_views.route('/artists/<string:artist_id>/profile-picture', methods=['POST'], strict_slashes=False)
def update_artist_profile_picture(artist_id: str) -> str:
    """Update the specified artist's profile picture"""
    if 'user_id' not in session:
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    artist = storage.get(Artist, artist_id)
    if not artist:
        return jsonify({"error": "Artist not found"}), 404

    # Check if the file is in the request
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    # Check if the file size is within the limit
    if request.content_length > MAX_CONTENT_LENGTH:
        return jsonify({"error": "File is too large"}), 400

    # Check the file's signature (magic number)
    file_type = imghdr.what(file)
    if not file_type or file_type not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Invalid file type"}), 400

    # Ensure upload directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Save the original image securely
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, f"{artist_id}_profile.jpg")
    file.save(file_path)

    # Generate a thumbnail for the profile picture
    thumbnail_path = os.path.join(UPLOAD_FOLDER, f"{artist_id}_profile_thumbnail.jpg")
    try:
        image = Image.open(file_path)
        image.thumbnail((500, 500))
        image.save(thumbnail_path)
    except Exception as e:
        return jsonify({"error": "Error processing image"}), 500

    artist.profile_picture_url = thumbnail_path
    storage.save()

    return jsonify({"message": "Profile picture updated successfully"}), 200
