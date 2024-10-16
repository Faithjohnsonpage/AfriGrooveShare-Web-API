#!/usr/bin/env python3
"""This module handles all default RestFul API actions for Users"""
from flask import request, jsonify, send_file, Response, session, current_app, url_for
from werkzeug.utils import secure_filename
from models.music import Music, ReleaseType
from models.artist import Artist
from models.genre import Genre
from models.user import User
from models.album import Album
from models import storage
from api.v1.views import app_views
import os
import mimetypes
from io import BytesIO
import magic
from flask import current_app
import logging
import imghdr
from PIL import Image


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('music.log')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


UPLOAD_FOLDER = 'api/v1/uploads/music'
COVER_UPLOAD_FOLDER = 'api/v1/uploads/music_cover'
MAX_CONTENT_LENGTH_IMAGE = 5 * 1000 * 1000
MAX_CONTENT_LENGTH = 15 * 1000 * 1000
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


@app_views.route('/music/upload', methods=['POST'], strict_slashes=False)
def upload_music() -> str:
    """Upload a new music file."""
    if 'user_id' not in session:
        logger.warning('Upload failed: No active session')
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    user = storage.get(User, user_id)

    if not user:
        logger.warning(f'Upload failed: User {user_id} not found')
        return jsonify({"error": "User not found"}), 404

    title = request.form.get('title')
    description = request.form.get('description')
    genre = request.form.get('genre')
    album_title = request.form.get('album')
    artist_name = request.form.get('artist')
    file = request.files.get('file')
    duration_str = request.form.get('duration')  # Expecting MM:SS format
    release_date = request.form.get('release_date')

    # Check if required fields are provided
    if not title or not genre or not file or not artist_name:
        logger.error(f'Upload failed: Missing required fields for user {user_id}')
        return jsonify({"error": "Missing required fields"}), 400

    artist = storage.filter_by(Artist, name=artist_name)
    if not artist:
        logger.error(f'Upload failed: Artist {artist_name} not found for user {user_id}')
        return jsonify({"error": "Artist not found"}), 404

    if artist.user_id != user.id:
        logger.error(f'Unauthorized upload attempt by user {user_id} for artist {artist_name}')
        return jsonify({"error": "Unauthorized: You are not the owner of this artist"}), 403

    # Check if the file size exceeds the limit
    if request.content_length > MAX_CONTENT_LENGTH:
        logger.error(f'Upload failed: File size exceeds the limit for user {user_id}')
        return jsonify({"error": "File is too large"}), 400

    # Check if the duration is in MM:SS format
    try:
        minutes, seconds = map(int, duration_str.split(':'))
        duration = (minutes * 60) + seconds  # Convert to total seconds
    except ValueError:
        logger.error(f'Upload failed: Invalid duration format by user {user_id}')
        return jsonify({"error": "Invalid duration format. Use MM:SS."}), 400

    # Validate the file's MIME type
    filename = secure_filename(file.filename)
    mime_type, _ = mimetypes.guess_type(filename)

    if mime_type != 'audio/mpeg':
        logger.error(f'Upload failed: Invalid file type {mime_type} for user {user_id}')
        return jsonify({"error": "Invalid file type, only MP3 is allowed"}), 400

    if not file.filename.endswith('.mp3'):
        logger.error(f'Upload failed: Invalid file extension {file.filename} for user {user_id}')
        return jsonify({"error": "Invalid file extension. Only .mp3 files are allowed."}), 400

    # Ensure the upload directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    music_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(music_path)
    logger.info(f'File {filename} saved successfully for user {user_id}')

    genre_obj = storage.filter_by(Genre, name=genre)
    if not genre_obj:
        logger.error(f'Upload failed: Genre {genre} not found for user {user_id}')
        return jsonify({"error": "Genre not found"}), 404

    new_music = Music()
    new_music.title = title
    new_music.artist_id = artist.id
    new_music.genre_id = genre_obj.id
    new_music.file_url = music_path
    new_music.duration = duration
    new_music.release_date = release_date

    if album_title:
        album = storage.filter_by(Album, title=album_title)
        if not album:
            logger.error(f'Upload failed: Album {album_title} not found for user {user_id}')
            return jsonify({"error": "Album not found"}), 404
        new_music.album_id = album.id
        new_music.release_type = ReleaseType.ALBUM
    else:
        new_music.description = description
        new_music.release_type = ReleaseType.SINGLE

    storage.new(new_music)
    storage.save()

    # Invalidate all music cache
    invalidate_all_music_cache()

    logger.info(f'Music {title} uploaded successfully by user {user_id}')

    # Build response links based on release type
    response_links = {
        "self": {"href": url_for('app_views.get_music_metadata', music_id=new_music.id, _external=True)},
        "stream": {"href": url_for('app_views.stream_music', music_id=new_music.id, _external=True)},
        "all_music": {"href": url_for('app_views.list_music_files', _external=True)}
    }

    # Add update_cover link only for singles
    if new_music.release_type == ReleaseType.SINGLE:
        response_links["update_cover"] = {
            "href": url_for('app_views.update_music_cover_image', music_id=new_music.id, _external=True)
        }

    response = jsonify({
        "message": "Music uploaded successfully",
        "musicId": new_music.id,
        "_links": response_links
    })
    return response, 201


@app_views.route('/music/<string:music_id>', methods=['GET'], strict_slashes=False)
def get_music_metadata(music_id: str) -> str:
    """Retrieve metadata for a specific music file."""
    
    cache_key = f"music_metadata_{music_id}"
    cached_music = current_app.cache.get(cache_key)

    if cached_music:
        logger.info(f"Serving cached metadata for music {music_id}.")
        return cached_music, 200

    music = storage.get(Music, music_id)
    if not music:
        logger.warning(f'Metadata request failed: Music {music_id} not found')
        return jsonify({"error": "Music not found"}), 404

    # Retrieve associated album, artist, and genre information
    album = storage.get(Album, music.album_id)
    artist = storage.get(Artist, music.artist_id)
    genre = storage.get(Genre, music.genre_id)

    # Prepare the metadata response
    music_data = {
        "id": music.id,
        "title": music.title,
        "artist": artist.name if artist else "Unknown",
        "album": album.title if album else None,
        "genre": genre.name if genre else "Unknown",
        "duration": f"{music.duration // 60}:{music.duration % 60:02d}",
        "fileUrl": music.file_url,
        "coverImageUrl": music.cover_image_url if music.cover_image_url else None,
        "releaseType": music.release_type.name,
        "description": music.description if music.description else None,
        "releaseDate": music.release_date.strftime('%Y-%m-%d') if music.release_date else None,
        "uploadDate": music.created_at.strftime('%Y-%m-%d')
    }

    music_data["_links"] = {
        "self": url_for('app_views.get_music_metadata', music_id=music.id, _external=True),
        "stream": url_for('app_views.stream_music', music_id=music.id, _external=True),
        "all_music": url_for('app_views.list_music_files', _external=True),
        "artist": url_for('app_views.get_artist', artist_id=music.artist_id, _external=True),
        "album": url_for('app_views.get_album', album_id=music.album_id, _external=True) if music.album_id else None,
    }

    response = jsonify(music_data)
    current_app.cache.set(cache_key, response, timeout=3600)
    logger.info(f'Metadata for music {music_id} retrieved and cached successfully')

    return response, 200

@app_views.route('/music/<string:music_id>/stream', methods=['GET'], strict_slashes=False)
def stream_music(music_id: str) -> Response:
    """Stream a specific music file by its ID"""
    music = storage.get(Music, music_id)
    
    if not music:
        logger.warning(f'Stream request failed: Music {music_id} not found')
        return jsonify({"error": "Music file not found"}), 404

    file_path = music.file_url
    
    if not file_path:
        logger.warning(f'Stream request failed: File for music {music_id} not found')
        return jsonify({"error": "File not found"}), 404

    def generate():
        with open(file_path, 'rb') as music_file:
            data = music_file.read(1024)
            while data:
                yield data
                data = music_file.read(1024)

    logger.info(f'Music {music_id} streaming started')
    return Response(generate(), mimetype="audio/mpeg")


@app_views.route('/music', methods=['GET'], strict_slashes=False)
def list_music_files() -> str:
    """Retrieve a list of music files with optional filters"""
    
    genre = request.args.get('genre')
    artist = request.args.get('artist')
    album = request.args.get('album')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    cache_key = f"all_music_page_{page}_limit_{limit}"
    cached_music_list = current_app.cache.get(cache_key)

    if cached_music_list:
        logger.info(f"Serving cached music list (page {page}, limit {limit}).")
        return cached_music_list, 200

    music = storage.all(Music)

    # Retrieve associated album, artist, and genre information
    album_obj = storage.filter_by(Album, title=album)
    artist_obj = storage.filter_by(Artist, name=artist)
    genre_obj = storage.filter_by(Genre, name=genre)

    if genre_obj:
        music = list(filter(lambda m: m.genre_id == genre_obj.id, music))
    if artist_obj:
        music = list(filter(lambda m: m.artist_id == artist_obj.id, music))
    if album_obj:
        music = list(filter(lambda m: m.album_id == album_obj.id, music))

    # Pagination
    total_count = len(music)
    start_index = (page - 1) * limit
    end_index = page * limit
    music_files = music[start_index:end_index]

    # Prepare the list of music metadata
    music_list = []
    for m in music_files:
        artist = storage.get(Artist, m.artist_id)
        album = storage.get(Album, m.album_id)
        genre = storage.get(Genre, m.genre_id)
    
        music_metadata = {
            "id": m.id,
            "title": m.title,
            "artist": artist.name if artist else "Unknown",
            "album": album.title if album else None,
            "genre": genre.name if genre else "Unknown",
            "duration": f"{m.duration // 60}:{m.duration % 60:02d}",
            "fileUrl": m.file_url,
            "coverImageUrl": m.cover_image_url if m.release_type == ReleaseType.SINGLE else \
                             (album.cover_image_url if album else None),
            "releaseType": m.release_type.value,
            "description": m.description if m.description else None,
            "releaseDate": m.release_date.strftime('%Y-%m-%d') if m.release_date else None,
            "uploadDate": m.created_at.strftime('%Y-%m-%d')
        }
        music_list.append(music_metadata)

    for music_metadata in music_list:
        music_metadata["_links"] = {
            "self": url_for('app_views.get_music_metadata', music_id=music_metadata["id"], _external=True),
            "stream": url_for('app_views.stream_music', music_id=music_metadata["id"], _external=True),
        }

    response = jsonify({
        "music": music_list,
        "total": total_count,
        "page": page,
        "limit": limit,
        "_links": {
            "self": url_for('app_views.list_music_files', page=page, limit=limit, _external=True),
            "next": url_for('app_views.list_music_files', page=page+1, limit=limit, _external=True) if end_index < total_count else None,
            "prev": url_for('app_views.list_music_files', page=page-1, limit=limit, _external=True) if page > 1 else None,
            "search": url_for('app_views.search_music', _external=True)
        }
    })

    current_app.cache.set(cache_key, response, timeout=3600)
    logger.info(f'List of music files (page {page}, limit {limit}) retrieved and cached successfully')

    return response, 200


#@app_views.route('/music/<music_id>', methods=['PUT'], strict_slashes=False)
#def update_music_metadata(music_id: str) -> str:
    #"""Attempt to update metadata for a specific music file (Not allowed)."""
    #return jsonify({"error": "Update operation not allowed"}), 403


#@app_views.route('/music/<music_id>', methods=['DELETE'], strict_slashes=False)
#def delete_music(music_id: str) -> str:
    #"""Attempt to delete a specific music file (operation not allowed)."""
    #return jsonify({"error": "Delete operation not allowed"}), 403


@app_views.route('/music/search', methods=['POST'], strict_slashes=False)
def search_music() -> str:
    """Search for music based on a query string that checks multiple fields."""
    # Retrieve the search query from the request data
    query_str = request.data.decode('utf-8').strip()

    if not query_str:
        logger.warning('Search request failed: No search query provided')
        return jsonify({"error": "No search query provided"}), 400

    # Fetch all relevant data
    music = storage.all(Music)
    artists = storage.all(Artist)
    albums = storage.all(Album)
    genres = storage.all(Genre)

    # Build the list of matching music
    matching_music = [
        m for m in music
        if query_str.lower() in m.title.lower() or
           query_str.lower() in (storage.get(Artist, m.artist_id).name if storage.get(Artist, m.artist_id) else "").lower() or
           query_str.lower() in (storage.get(Album, m.album_id).title if storage.get(Album, m.album_id) else "").lower() or
           query_str.lower() in (storage.get(Genre, m.genre_id).name if storage.get(Genre, m.genre_id) else "").lower()
    ]

    if not matching_music:
        return jsonify({"error": "No music found"}), 404

    # Prepare response
    music_list = [
        {
            "id": m.id,
            "title": m.title,
            "artist": storage.get(Artist, m.artist_id).name if storage.get(Artist, m.artist_id) else "Unknown",
            "fileUrl": m.file_url,
            "duration": f"{m.duration // 60}:{m.duration % 60:02d}"
        } for m in matching_music
    ]

    for music in music_list:
        music["_links"] = {
            "self": url_for('app_views.get_music_metadata', music_id=music["id"], _external=True),
            "stream": url_for('app_views.stream_music', music_id=music["id"], _external=True),
        }

    response = jsonify({
        "results": music_list,
        "_links": {
            "all_music": url_for('app_views.list_music_files', _external=True)
        }
    })

    logger.info(f'Search query "{query_str}" completed successfully')
    return jsonify(music_list), 200


@app_views.route('/music/<string:music_id>/cover-image', methods=['POST'], strict_slashes=False)
def update_music_cover_image(music_id: str) -> str:
    """Update the specified music's cover image"""
    logger.info(f"Attempting to update cover image for music with ID {music_id}")

    if 'user_id' not in session:
        logger.warning("No active session for cover image update")
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        logger.warning("Unauthorized cover image update attempt")
        return jsonify({"error": "Unauthorized"}), 401

    music = storage.get(Music, music_id)
    if not music:
        logger.error(f"Music with ID {music_id} not found")
        return jsonify({"error": "Music not found"}), 404

    if music.release_type != ReleaseType.SINGLE:
        logger.warning(f"Cannot update cover image for non-single music with ID {music_id}")
        return jsonify({"error": "Cover image can only be updated for singles"}), 400

    # Check if the file is in the request
    file = request.files.get('file')
    if not file:
        logger.warning(f"No file uploaded for music {music_id} cover image update")
        return jsonify({"error": "No file uploaded"}), 400

    # Check if the file size is within the limit
    if request.content_length > MAX_CONTENT_LENGTH_IMAGE:
        logger.warning(f"File too large for music {music_id} cover image update")
        return jsonify({"error": "File is too large"}), 400

    # Check the file's signature (magic number)
    file_type = imghdr.what(file)
    if not file_type or file_type not in ALLOWED_EXTENSIONS:
        logger.warning(f"Invalid file type for music {music_id} cover image update")
        return jsonify({"error": "Invalid file type"}), 400

    # Ensure upload directory exists
    os.makedirs(COVER_UPLOAD_FOLDER, exist_ok=True)

    # Save the original image securely
    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1].lower()
    file_path = os.path.join(COVER_UPLOAD_FOLDER, f"{music_id}_cover{file_ext}")
    file.save(file_path)

    # Generate a thumbnail for the cover image
    thumbnail_path = os.path.join(COVER_UPLOAD_FOLDER, f"{music_id}_cover_thumbnail{file_ext}")
    try:
        image = Image.open(file_path)
        image.thumbnail((500, 500))
        image.save(thumbnail_path)
    except Exception as e:
        logger.error(f"Error processing image for music {music_id}: {str(e)}")
        return jsonify({"error": "Error processing image"}), 500

    # Update the music object with the new cover image URL
    music.cover_image_url = file_path
    music.cover_thumbnail_url = thumbnail_path
    storage.save()

    # Invalidate all music cache
    invalidate_all_music_cache()
    current_app.cache.delete(f"music_{music_id}")
    logger.info(f"Invalidated cache for music {music_id}")

    logger.info(f"Cover image updated successfully for music {music_id}")

    response = jsonify({
        "message": "Cover image updated successfully",
        "_links": {
            "music": url_for('app_views.get_music_metadata', music_id=music_id, _external=True),
            "all_music": url_for('app_views.list_music_files', _external=True)
        }
    })
    return response, 200


def invalidate_all_music_cache():
    """Invalidate all cache entries related to music."""
    cache = current_app.cache
    pattern = "flask_cache_all_music_*"

    # Get all keys matching the pattern
    keys_to_delete = [key.decode('utf-8') for key in cache.cache._read_client.keys(pattern)]

    if keys_to_delete:
        # Adjust the keys for deletion by removing any prefix if necessary
        adjusted_keys = [key.replace('flask_cache_', '', 1) for key in keys_to_delete]
        cache.delete_many(*adjusted_keys)
        logger.info(f"Invalidated {len(adjusted_keys)} cache entries for all music")
    else:
        logger.info("No cache entries found to invalidate for all music")
