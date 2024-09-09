#!/usr/bin/env python3
from flask import jsonify, request, session
from models import storage
from models.album import Album
from models.artist import Artist
from models.user import User
from datetime import datetime
from api.v1.views import app_views
from werkzeug.utils import secure_filename
from PIL import Image
import os
import imghdr
import uuid


UPLOAD_FOLDER = 'api/v1/uploads/album_cover'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_CONTENT_LENGTH = 5 * 1000 * 1000


@app_views.route('/albums', methods=['POST'], strict_slashes=False)
def create_album() -> str:
    """Create a new album"""
    # Check if the user is logged in
    if 'user_id' not in session:
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    user = storage.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Retrieve artist_id from query parameters
    artist_id = request.args.get('artist_id')
    artist = storage.get(Artist, artist_id)

    if not artist:
        return jsonify({"error": "Artist not found"}), 404

    if artist.user_id != user.id:
        return jsonify({"error": "Unauthorized"}), 403

    # Get album details from form data
    title = request.form.get('title')
    release_date = request.form.get('release_date')

    if not title:
        return jsonify({"error": "Missing album title"}), 400

    # Prompt user to review album details before finalizing (commented out)
    #confirmation = request.form.get('confirm')
    #if not confirmation or confirmation.lower() != 'yes':
        #message =  "Please review your album details and confirm before submission."
        #return jsonify({"message": message}), 200

    # Convert release_date from string to date, if provided
    try:
        release_date = datetime.strptime(release_date, '%Y-%m-%d').date() if release_date else None
    except ValueError:
        return jsonify({"error": "Invalid release date format, use YYYY-MM-DD"}), 400

    album = Album()
    album.title = title
    album.artist_id = artist_id
    album.release_date = release_date
    storage.new(album)
    storage.save()

    return jsonify({"message": "Album created successfully", "albumId": album.id}), 201

@app_views.route('/albums/<string:album_id>', methods=['GET'], strict_slashes=False)
def get_album(album_id: str) -> str:
    """Retrieve an album by ID"""
    if 'user_id' not in session:
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    album = storage.get(Album, album_id)
    if not album:
        return jsonify({"error": "Album not found"}), 404

    artist = storage.get(Artist, album.artist_id)
    print('this')

    return jsonify({
        "album": {
            "id": album.id,
            "title": album.title,
            "artist": {
                "id": album.artist_id,
                "name": artist.name
            },
            "releaseDate": str(album.release_date),
        }
    }), 200


# Commenting out or removing these routes to make albums immutable

# @app_views.route('/albums/<album_id>', methods=['PUT'], strict_slashes=False)
# def update_album(album_id):
#     return jsonify({"error": "Album modifications are not allowed."}), 403


# @app_views.route('/albums/<album_id>', methods=['DELETE'], strict_slashes=False)
# def delete_album(album_id):
#     return jsonify({"error": "Album deletion is not allowed."}), 403


@app_views.route('/albums', methods=['GET'], strict_slashes=False)
def list_albums():
    """List all albums"""
    albums = storage.all(Album)
    print('that')

    # Prepare list of albums with artist details
    return jsonify({
        "albums": [
            {
                "id": album.id,
                "title": album.title,
                "artist": {
                    "id": album.artist_id,
                    "name": storage.get(Artist, album.artist_id).name
                },
                "releaseDate": str(album.release_date),
            } for album in albums
        ]
    }), 200


@app_views.route('/albums/<string:album_id>/cover-image', methods=['POST'], strict_slashes=False)
def update_album_cover_image(album_id: str) -> str:
    """Update the specified album's cover image"""
    if 'user_id' not in session:
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    album = storage.get(Album, album_id)
    if not album:
        return jsonify({"error": "Album not found"}), 404

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
    file_path = os.path.join(UPLOAD_FOLDER, f"{album_id}_cover.jpg")
    file.save(file_path)

    # Generate a thumbnail for the cover image
    thumbnail_path = os.path.join(UPLOAD_FOLDER, f"{album_id}_cover_thumbnail.jpg")
    try:
        image = Image.open(file_path)
        image.thumbnail((500, 500))
        image.save(thumbnail_path)
    except Exception as e:
        return jsonify({"error": "Error processing image"}), 500

    album.cover_image_url = thumbnail_path
    storage.save()

    return jsonify({"message": "Cover image updated successfully"}), 200
