#!/usr/bin/env python3
from flask import jsonify, request, session, current_app
from models import storage
from models.album import Album
from models.artist import Artist
from models.user import User
from models.music import Music
from datetime import datetime
from api.v1.views import app_views
from werkzeug.utils import secure_filename
from PIL import Image
import os
import imghdr
import uuid
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('album.log')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


UPLOAD_FOLDER = 'api/v1/uploads/album_cover'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_CONTENT_LENGTH = 5 * 1000 * 1000


@app_views.route('/albums', methods=['POST'], strict_slashes=False)
def create_album() -> str:
    """Create a new album"""
    # Check if the user is logged in
    if 'user_id' not in session:
        logger.warning("No active session for album creation")
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    user = storage.get(User, user_id)

    if not user:
        logger.error(f"User with ID {user_id} not found")
        return jsonify({"error": "User not found"}), 404

    # Retrieve artist_id from query parameters
    artist_id = request.args.get('artist_id')
    artist = storage.get(Artist, artist_id)

    if not artist:
        logger.error(f"Artist with ID {artist_id} not found")
        return jsonify({"error": "Artist not found"}), 404

    if artist.user_id != user.id:
        logger.warning(f"Unauthorized album creation attempt by user {user_id} for artist {artist_id}")
        return jsonify({"error": "Unauthorized"}), 403

    # Get album details from form data
    title = request.form.get('title')
    description = request.form.get('description')
    release_date = request.form.get('release_date')

    if not title:
        logger.warning("Missing album title in creation request")
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
        logger.error(f"Invalid release date format: {release_date}")
        return jsonify({"error": "Invalid release date format, use YYYY-MM-DD"}), 400

    album = Album()
    album.title = title
    album.artist_id = artist_id
    album.description = description
    album.release_date = release_date
    storage.new(album)
    storage.save()

    # Invalidate all albums cache
    invalidate_all_albums_cache()

    logger.info(f"Album '{title}' created successfully with ID {album.id}")
    return jsonify({"message": "Album created successfully", "albumId": album.id}), 201


@app_views.route('/albums/<string:album_id>', methods=['GET'], strict_slashes=False)
def get_album(album_id: str) -> str:
    """Retrieve an album by ID along with its associated music"""

    cache_key = f"album_{album_id}"
    cached_album = current_app.cache.get(cache_key)

    if cached_album:
        logger.info(f"Serving cached album {album_id}.")
        return cached_album, 200

    album = storage.get(Album, album_id)
    if not album:
        logger.error(f"Album with ID {album_id} not found")
        return jsonify({"error": "Album not found"}), 404

    artist = storage.get(Artist, album.artist_id)

    # Retrieve all music associated with the album
    music = storage.all(Music)
    music_list = list(filter(lambda m: m.album_id == album_id, music))

    # Prepare the music data for the response
    music_data = []
    for music in music_list:
        music_data.append({
            "id": music.id,
            "title": music.title,
            "duration": music.duration,
            "file_url": music.file_url,
        })

    response = jsonify({
        "album": {
            "id": album.id,
            "title": album.title,
            "artist": {
                "id": artist.id,
                "name": artist.name
            },
            "releaseDate": str(album.release_date),
            "music": music_data
        }
    })

    current_app.cache.set(cache_key, response, timeout=3600)
    logger.info(f"Album '{album.title}' retrieved and cached successfully.")
    
    return response, 200


# Commenting out or removing these routes to make albums immutable

# @app_views.route('/albums/<album_id>', methods=['PUT'], strict_slashes=False)
# def update_album(album_id):
#     return jsonify({"error": "Album modifications are not allowed."}), 403


# @app_views.route('/albums/<album_id>', methods=['DELETE'], strict_slashes=False)
# def delete_album(album_id):
#     return jsonify({"error": "Album deletion is not allowed."}), 403


@app_views.route('/albums', methods=['GET'], strict_slashes=False)
def list_albums() -> str:
    """List all albums"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    cache_key = f"all_albums_page_{page}_limit_{limit}"
    cached_albums = current_app.cache.get(cache_key)

    if cached_albums:
        logger.info(f"Serving cached albums for page {page} with limit {limit}.")
        return cached_albums, 200

    albums = storage.all(Album)

    # Pagination
    total_count = len(albums)
    start_index = (page - 1) * limit
    end_index = page * limit
    album_files = albums[start_index:end_index]

    response = jsonify({
        "albums": [
            {
                "id": album.id,
                "title": album.title,
                "artist": {
                    "id": album.artist_id,
                    "name": storage.get(Artist, album.artist_id).name
                },
                "releaseDate": str(album.release_date),
            } for album in album_files
        ],
        "total": total_count,
        "page": page,
        "limit": limit
    })

    current_app.cache.set(cache_key, response, timeout=3600)
    logger.info(f"Albums for page {page} with limit {limit} retrieved and cached successfully.")

    return response, 200


@app_views.route('/albums/<string:album_id>/cover-image', methods=['POST'], strict_slashes=False)
def update_album_cover_image(album_id: str) -> str:
    """Update the specified album's cover image"""
    logger.info(f"Attempting to update cover image for album with ID {album_id}")

    if 'user_id' not in session:
        logger.warning("No active session for cover image update")
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        logger.warning("Unauthorized cover image update attempt")
        return jsonify({"error": "Unauthorized"}), 401

    album = storage.get(Album, album_id)
    if not album:
        logger.error(f"Album with ID {album_id} not found")
        return jsonify({"error": "Album not found"}), 404

    # Check if the file is in the request
    file = request.files.get('file')
    if not file:
        logger.warning(f"No file uploaded for album {album_id} cover image update")
        return jsonify({"error": "No file uploaded"}), 400

    # Check if the file size is within the limit
    if request.content_length > MAX_CONTENT_LENGTH:
        logger.warning(f"File too large for album {album_id} cover image update")
        return jsonify({"error": "File is too large"}), 400

    # Check the file's signature (magic number)
    file_type = imghdr.what(file)
    if not file_type or file_type not in ALLOWED_EXTENSIONS:
        logger.warning(f"Invalid file type for album {album_id} cover image update")
        return jsonify({"error": "Invalid file type"}), 400

    # Ensure upload directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Save the original image securely
    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1].lower()
    file_path = os.path.join(UPLOAD_FOLDER, f"{album_id}_cover{file_ext}")
    file.save(file_path)

    # Generate a thumbnail for the cover image
    thumbnail_path = os.path.join(UPLOAD_FOLDER, f"{album_id}_cover_thumbnail{file_ext}")
    try:
        image = Image.open(file_path)
        image.thumbnail((500, 500))
        image.save(thumbnail_path)
    except Exception as e:
        logger.error(f"Error processing image for album {album_id}: {str(e)}")
        return jsonify({"error": "Error processing image"}), 500

    album.cover_image_url = thumbnail_path
    storage.save()

    # Invalidate all albums cache
    invalidate_all_albums_cache()

    current_app.cache.delete(f"album_{album_id}")
    logger.info(f"Invalidated cache for album {album_id}")
    logger.info(f"Cover image updated successfully for album {album_id}")
    return jsonify({"message": "Cover image updated successfully"}), 200


def invalidate_all_albums_cache():
    """Invalidate all cache entries related to albums."""
    cache = current_app.cache
    pattern = "flask_cache_all_albums_*"

    # Get all keys matching the pattern
    keys_to_delete = [key.decode('utf-8') for key in cache.cache._read_client.keys(pattern)]

    if keys_to_delete:
        # Adjust the keys for deletion by removing any prefix if necessary
        adjusted_keys = [key.replace('flask_cache_', '', 1) for key in keys_to_delete]
        cache.delete_many(*adjusted_keys)
        logger.info(f"Invalidated {len(adjusted_keys)} cache entries for all albums")
    else:
        logger.info("No cache entries found to invalidate for all albums")
