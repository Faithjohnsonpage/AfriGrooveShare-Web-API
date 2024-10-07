#!/usr/bin/env python3
from flask import jsonify, request, session, current_app
from models import storage
from models.artist import Artist
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
file_handler = logging.FileHandler('artist.log')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


UPLOAD_FOLDER = 'api/v1/uploads/artist_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_CONTENT_LENGTH = 5 * 1000 * 1000


@app_views.route('/artists', methods=['POST'], strict_slashes=False)
def create_artist() -> str:
    """Create a new artist"""
    if 'user_id' not in session:
        logger.warning("Unauthorized access attempt to create artist.")
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        logger.error("Unauthorized access, session found but user_id missing.")
        return jsonify({"error": "Unauthorized"}), 401

    name = request.form.get('name')
    bio = request.form.get('bio')
    if not name:
        logger.warning("Artist creation failed due to missing name.")
        return jsonify({"error": "Missing name"}), 400

    artist = Artist()
    artist.name = name
    artist.bio = bio
    artist.user_id = user_id
    storage.new(artist)
    storage.save()

    # Invalidate all artists cache
    invalidate_all_artists_cache()

    logger.info(f"Artist (ID: {artist.id}) created successfully by user {user_id}.")
    return jsonify({"message": "Artist created successfully", "artistId": artist.id}), 201


@app_views.route('/artists/<string:artist_id>', methods=['GET'], strict_slashes=False)
def get_artist(artist_id: str) -> str:
    """Retrieve an artist by ID"""

    cache_key = f"artist_{artist_id}"
    cached_artist = current_app.cache.get(cache_key)

    if cached_artist:
        logger.info(f"Serving cached artist {artist_id}.")
        return cached_artist, 200

    artist = storage.get(Artist, artist_id)
    if not artist:
        logger.warning(f"Artist with ID {artist_id} not found.")
        return jsonify({"error": "Artist not found"}), 404

    response = jsonify({
        "artist": {
            "id": artist.id,
            "name": artist.name,
            "bio": artist.bio,
            "profile_picture_url": artist.profile_picture_url
        }
    })

    current_app.cache.set(cache_key, response, timeout=3600)
    logger.info(f"Artist (ID: {artist_id}) retrieved and cached.")
    
    return response, 200


@app_views.route('/artists/<string:artist_id>', methods=['PUT'], strict_slashes=False)
def update_artist(artist_id: str) -> str:
    """Update an artist by ID"""
    if 'user_id' not in session:
        logger.warning("Unauthorized access attempt to update artist.")
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        logger.error("Unauthorized access, session found but user_id missing.")
        return jsonify({"error": "Unauthorized"}), 401

    artist = storage.get(Artist, artist_id)
    if not artist:
        logger.warning(f"Artist with ID {artist_id} not found.")
        return jsonify({"error": "Artist not found"}), 404

    name = request.form.get('name')
    bio = request.form.get('bio')
    if name:
        artist.name = name
    if bio:
        artist.bio = bio

    storage.save()

    # Invalidate all artists cache
    invalidate_all_artists_cache()

    current_app.cache.delete(f"artist_{artist_id}")
    logger.info(f"Invalidated cache for artist {artist_id}")
    logger.info(f"Artist (ID: {artist_id}) updated by user {user_id}.")
    return jsonify({"message": "Artist updated successfully"}), 200


@app_views.route('/artists/<string:artist_id>', methods=['DELETE'], strict_slashes=False)
def delete_artist(artist_id: str) -> str:
    """Delete an artist by ID"""
    if 'user_id' not in session:
        logger.warning("Unauthorized access attempt to delete artist.")
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        logger.error("Unauthorized access, session found but user_id missing.")
        return jsonify({"error": "Unauthorized"}), 401

    artist = storage.get(Artist, artist_id)
    if not artist:
        logger.warning(f"Artist with ID {artist_id} not found.")
        return jsonify({"error": "Artist not found"}), 404

    storage.delete(artist)
    storage.save()

    # Invalidate all artists cache
    invalidate_all_artists_cache()

    current_app.cache.delete(f"artist_{artist_id}")
    logger.info(f"Invalidated cache for artist {artist_id}")
    logger.info(f"Artist (ID: {artist_id}) deleted by user {user_id}.")
    return jsonify({"message": "Artist deleted successfully"}), 200


@app_views.route('/artists', methods=['GET'], strict_slashes=False)
def list_artists():
    """List all artists with caching"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    cache_key = f"all_artists_{page}_limit_{limit}"
    cached_artists = current_app.cache.get(cache_key)

    if cached_artists:
        logger.info(f"Serving cached list of artists: page {page}, limit {limit}.")
        return cached_artists, 200

    artists = storage.all(Artist)

    # Pagination
    total_count = len(artists)
    start_index = (page - 1) * limit
    end_index = page * limit
    artists_files = artists[start_index:end_index]

    response = jsonify({
        "artists": [
            {
                "id": artist.id,
                "name": artist.name,
                "profile_picture_url": artist.profile_picture_url
            } for artist in artists_files
        ],
        "total": total_count,
        "page": page,
        "limit": limit
    })

    current_app.cache.set(cache_key, response, timeout=3600)
    logger.info(f"List of artists cached for page {page}, limit {limit}.")
    return response, 200


@app_views.route('/artists/<string:artist_id>/profile-picture', methods=['POST'], strict_slashes=False)
def update_artist_profile_picture(artist_id: str) -> str:
    """Update the specified artist's profile picture"""
    if 'user_id' not in session:
        logger.warning("Unauthorized access attempt to update artist profile picture.")
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        logger.error("Unauthorized access, session found but user_id missing.")
        return jsonify({"error": "Unauthorized"}), 401

    artist = storage.get(Artist, artist_id)
    if not artist:
        logger.warning(f"Artist with ID {artist_id} not found.")
        return jsonify({"error": "Artist not found"}), 404

    # Check if the file is in the request
    file = request.files.get('file')
    if not file:
        logger.warning("No file uploaded for artist profile picture update.")
        return jsonify({"error": "No file uploaded"}), 400

    # Check if the file size is within the limit
    if request.content_length > MAX_CONTENT_LENGTH:
        logger.warning("Uploaded file exceeds maximum allowed size.")
        return jsonify({"error": "File is too large"}), 400

    # Check the file's signature (magic number)
    file_type = imghdr.what(file)
    if not file_type or file_type not in ALLOWED_EXTENSIONS:
        logger.warning("Invalid file type uploaded.")
        return jsonify({"error": "Invalid file type"}), 400

    # Ensure upload directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Save the original image securely
    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1].lower()
    file_path = os.path.join(UPLOAD_FOLDER, f"{artist_id}_profile{file_ext}")
    file.save(file_path)

    # Generate a thumbnail for the profile picture
    thumbnail_path = os.path.join(UPLOAD_FOLDER, f"{artist_id}_profile_thumbnail{file_ext}")
    try:
        image = Image.open(file_path)
        image.thumbnail((500, 500))
        image.save(thumbnail_path)
    except Exception as e:
        logger.error(f"Error processing image for artist {artist_id}: {str(e)}")
        return jsonify({"error": "Error processing image"}), 500

    artist.profile_picture_url = thumbnail_path
    storage.save()

    # Invalidate all artists cache
    invalidate_all_artists_cache()

    current_app.cache.delete(f"artist_{artist_id}")
    logger.info(f"Invalidated cache for artist {artist_id}")
    logger.info(f"Profile picture for artist {artist_id} updated successfully.")
    return jsonify({"message": "Profile picture updated successfully"}), 200


def invalidate_all_artists_cache():
    """Invalidate all cache entries related to artists."""
    cache = current_app.cache
    pattern = "flask_cache_all_artists_*"

    # Get all keys matching the pattern
    keys_to_delete = [key.decode('utf-8') for key in cache.cache._read_client.keys(pattern)]

    if keys_to_delete:
        # Adjust the keys for deletion by removing any prefix if necessary
        adjusted_keys = [key.replace('flask_cache_', '', 1) for key in keys_to_delete]
        cache.delete_many(*adjusted_keys)
        logger.info(f"Invalidated {len(adjusted_keys)} cache entries for all artists")
    else:
        logger.info("No cache entries found to invalidate for all artists")
