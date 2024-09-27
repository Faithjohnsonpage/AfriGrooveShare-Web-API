#!/usr/bin/env python3
"""This module handles all default RestFul API actions for Users"""
from flask import request, jsonify, send_file, Response, session
from werkzeug.utils import secure_filename
from models.music import Music
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


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("music.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


UPLOAD_FOLDER = 'api/v1/uploads/music'
MAX_CONTENT_LENGTH = 10 * 1000 * 1000


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
    album = request.form.get('album')
    artist_name = request.form.get('artist')
    file = request.files.get('file')
    duration_str = request.form.get('duration')  # Expecting MM:SS format

    # Check if required fields are provided
    if not title or not genre or not file:
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

    album = storage.filter_by(Album, title=album)
    if not album:
        logger.error(f'Upload failed: Album {album} not found for user {user_id}')
        return jsonify({"error": "Album not found"}), 404

    genre_obj = storage.filter_by(Genre, name=genre)
    if not genre_obj:
        logger.error(f'Upload failed: Genre {genre} not found for user {user_id}')
        return jsonify({"error": "Genre not found"}), 404

    new_music = Music()
    new_music.title = title
    new_music.artist_id = artist.id
    new_music.album_id = album.id
    new_music.genre_id = genre_obj.id
    new_music.file_url = music_path
    #new_music.description = description
    new_music.duration = duration
    storage.new(new_music)
    storage.save()

    logger.info(f'Music {title} uploaded successfully by user {user_id}')
    return jsonify({"message": "Music uploaded successfully", "musicId": new_music.id}), 201


@app_views.route('/music/<music_id>', methods=['GET'], strict_slashes=False)
def get_music_metadata(music_id: str) -> str:
    """Retrieve metadata for a specific music file."""
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
        "album": album.title if album else "Unknown",
        "genre": genre.name if genre else "Unknown",
        "duration": f"{music.duration // 60}:{music.duration % 60:02d}",
        "fileUrl": music.file_url,
        "coverImageUrl": album.cover_image_url if album else None,
        "uploadDate": music.created_at.strftime('%Y-%m-%d')
    }

    logger.info(f'Metadata for music {music_id} retrieved successfully')
    return jsonify(music_data), 200


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

    music = storage.all(Music)

    # Retrieve associated album, artist, and genre information
    album = storage.filter_by(Album, title=album)
    artist = storage.filter_by(Artist, name=artist)
    genre = storage.filter_by(Genre, name=genre)

    if genre:
        music = list(filter(lambda m: m.genre_id == genre.id, music))
    if artist:
        music = list(filter(lambda m: m.artist_id == artist.id, music))
    if album:
        music = list(filter(lambda m: m.album_id == album.id, music))

    # Pagination
    total_count = len(music)
    start_index = (page - 1) * limit
    end_index = page * limit
    music_files = music[start_index:end_index]

    # Prepare the list of music metadata
    music_list = []
    for m in music_files:
        # Fetch the related objects based on foreign keys
        artist = storage.get(Artist, m.artist_id)
        album = storage.get(Album, m.album_id)
        genre = storage.get(Genre, m.genre_id)
    
        # Prepare metadata for each music file
        music_metadata = {
            "id": m.id,
            "title": m.title,
            "artist": artist.name if artist else "Unknown",
            "album": album.title if album else "Unknown",
            "genre": genre.name if genre else "Unknown",
            "duration": f"{m.duration // 60}:{m.duration % 60:02d}",
            "fileUrl": m.file_url,
            "coverImageUrl": album.cover_image_url if album else None,
            "uploadDate": m.created_at.strftime('%Y-%m-%d')
        }
        music_list.append(music_metadata)

    logger.info(f'List of music files retrieved successfully (page {page}, limit {limit})')
    return jsonify({
        "music": music_list,
        "total": total_count,
        "page": page,
        "limit": limit
    }), 200


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
            "album": storage.get(Album, m.album_id).title if storage.get(Album, m.album_id) else "Unknown",
            "genre": storage.get(Genre, m.genre_id).name if storage.get(Genre, m.genre_id) else "Unknown",
            "duration": f"{m.duration // 60}:{m.duration % 60:02d}",
            "uploadDate": m.created_at.strftime('%Y-%m-%d'),
            "file_url": m.file_url
        } for m in matching_music
    ]

    logger.info(f'Search query "{query_str}" completed successfully')
    return jsonify(music_list), 200
