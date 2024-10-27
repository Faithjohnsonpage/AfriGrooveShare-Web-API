#!/usr/bin/env python3
from flask import jsonify, request, session, current_app, url_for
from models import storage
from models.playlist import Playlist
from models.music import Music
from models.artist import Artist
from models.album import Album
from api.v1.views import app_views
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('playlist.log')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


@app_views.route('/playlist/create', methods=['POST'], strict_slashes=False)
def create_playlist():
    """Create a new playlist"""
    if 'user_id' not in session:
        logger.warning('Attempt to create playlist without active session')
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        logger.warning('Unauthorized playlist creation attempt')
        return jsonify({"error": "Unauthorized"}), 401

    name = request.form.get('name')
    description = request.form.get('description')

    if not name:
        logger.warning('Missing name in playlist creation request')
        return jsonify({"error": "Missing name"}), 400

    playlist = Playlist()
    playlist.name = name
    playlist.description = description
    playlist.user_id = user_id
    storage.new(playlist)
    storage.save()

    # Invalidate all playlists cache
    invalidate_all_playlists_cache()

    logger.info(f'Playlist created successfully: {playlist.id}')

    response = jsonify({
        "message": "Playlist created successfully",
        "playlistId": playlist.id,
        "_links": {
            "self": url_for('app_views.get_playlist', playlist_id=playlist.id, _external=True),
            "update": url_for('app_views.update_playlist', playlist_id=playlist.id, _external=True),
            "delete": url_for('app_views.delete_playlist', playlist_id=playlist.id, _external=True),
            "all_playlists": url_for('app_views.list_playlists', _external=True)
        }
    })
    return response, 201


@app_views.route('/playlists/<string:playlist_id>', methods=['POST'], strict_slashes=False)
def update_playlist(playlist_id: str) -> str:
    """Update a playlist, either by editing or adding music"""
    if 'user_id' not in session:
        logger.warning(f'Attempt to update playlist {playlist_id} without active session')
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        logger.warning(f'Unauthorized update attempt for playlist {playlist_id}')
        return jsonify({"error": "Unauthorized"}), 401

    playlist = storage.get(Playlist, playlist_id)
    if not playlist:
        logger.error(f'Playlist {playlist_id} not found')
        return jsonify({"error": "Playlist not found"}), 404

    # Ensure the user is the owner of the playlist
    if playlist.user_id != user_id:
        logger.warning(f'Unauthorized update attempt by user {user_id} on playlist {playlist_id}')
        return jsonify({"error": "Unauthorized to update this playlist"}), 403

    action = request.form.get('action')
    name = request.form.get('name')
    description = request.form.get('description')

    # Handle playlist name and description editing
    if action == 'edit':
        if name:
            playlist.name = name
        if description:
            playlist.description = description

        storage.save()

        # Invalidate all playlists cache
        invalidate_all_playlists_cache()

        current_app.cache.delete(f"playlist_{playlist_id}")
        current_app.cache.delete(f"playlist_{playlist_id}_user_{user_id}")
        logger.info(f"Invalidated cache for playlist {playlist_id}")
        logger.info(f'Playlist {playlist_id} updated successfully')

        response = jsonify({
            "message": "Playlist updated successfully",
            "_links": {
                "self": url_for('app_views.get_playlist', playlist_id=playlist_id, _external=True),
                "delete": url_for('app_views.delete_playlist', playlist_id=playlist_id, _external=True),
                "all_playlists": url_for('app_views.list_playlists', _external=True)
            }
        })
        return response, 200

    # Handle adding music to the playlist
    elif action == 'add_music':
        music_ids = request.form.getlist('musicIds')

        if not music_ids:
            logger.warning('No music provided for adding to playlist')
            return jsonify({"error": "No music provided"}), 400

        for music_id in music_ids:
            music = storage.get(Music, music_id)
            if music:
                try:
                    playlist.add_music(Playlist, playlist_id, music)
                except ValueError as e:
                    logger.error(f'Error adding music {music_id} to playlist {playlist_id}: {e}')
                    return jsonify({"error": str(e)}), 400
            else:
                logger.error(f'Music with id {music_id} not found')
                return jsonify({"error": f"Music with id {music_id} not found"}), 404

        # Invalidate all playlists cache
        invalidate_all_playlists_cache()

        current_app.cache.delete(f"playlist_{playlist_id}")
        current_app.cache.delete(f"playlist_{playlist_id}_user_{user_id}")
        logger.info(f"Invalidated cache for playlist {playlist_id}")
        logger.info(f'Music added to playlist {playlist_id} successfully')

        response = jsonify({
            "message": "Music added to playlist successfully",
            "_links": {
                "self": url_for('app_views.get_playlist', playlist_id=playlist_id, _external=True),
                "update": url_for('app_views.update_playlist', playlist_id=playlist_id, _external=True),
                "delete": url_for('app_views.delete_playlist', playlist_id=playlist_id, _external=True),
                "all_playlists": url_for('app_views.list_playlists', _external=True)
            }
        })
        return response, 200

    # Handle removing music from the playlist
    elif action == 'remove_music':
        music_ids = request.form.getlist('musicIds')

        if not music_ids:
            logger.warning('No music provided for removal from playlist')
            return jsonify({"error": "No music provided"}), 400

        for music_id in music_ids:
            music = storage.get(Music, music_id)
            if music:
                try:
                    playlist.remove_music(Playlist, playlist_id, music)
                except ValueError as e:
                    logger.error(f'Error removing music {music_id} from playlist {playlist_id}: {e}')
                    return jsonify({"error": str(e)}), 400
            else:
                logger.error(f'Music with id {music_id} not found')
                return jsonify({"error": f"Music with id {music_id} not found"}), 404

        # Invalidate all playlists cache
        invalidate_all_playlists_cache()

        current_app.cache.delete(f"playlist_{playlist_id}")
        current_app.cache.delete(f"playlist_{playlist_id}_user_{user_id}")
        logger.info(f"Invalidated cache for playlist {playlist_id}")
        logger.info(f'Music removed from playlist {playlist_id} successfully')

        response = jsonify({
            "message": "Music removed from playlist successfully",
            "_links": {
                "self": url_for('app_views.get_playlist', playlist_id=playlist_id, _external=True),
                "update": url_for('app_views.update_playlist', playlist_id=playlist_id, _external=True),
                "delete": url_for('app_views.delete_playlist', playlist_id=playlist_id, _external=True),
                "all_playlists": url_for('app_views.list_playlists', _external=True)
            }
        })
        return response, 200

    logger.warning('Invalid action provided in playlist update request')
    return jsonify({"error": "Invalid action provided"}), 400


@app_views.route('/playlists/<string:playlist_id>', methods=['DELETE'], strict_slashes=False)
def delete_playlist(playlist_id: str) -> str:
    """Delete a playlist"""
    # Check if the user is logged in
    if 'user_id' not in session:
        logger.warning(f'Attempt to delete playlist {playlist_id} without active session')
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        logger.warning(f'Unauthorized delete attempt for playlist {playlist_id}')
        return jsonify({"error": "Unauthorized"}), 401

    # Retrieve the playlist
    playlist = storage.get(Playlist, playlist_id)
    if not playlist:
        logger.error(f'Playlist {playlist_id} not found')
        return jsonify({"error": "Playlist not found"}), 404

    # Ensure the user is the owner of the playlist
    if playlist.user_id != user_id:
        logger.warning(f'Unauthorized delete attempt by user {user_id} on playlist {playlist_id}')
        return jsonify({"error": "Unauthorized to delete this playlist"}), 403

    # Delete the playlist
    storage.delete(playlist)
    storage.save()

    # Invalidate all playlists cache
    invalidate_all_playlists_cache()

    current_app.cache.delete(f"playlist_{playlist_id}")
    current_app.cache.delete(f"playlist_{playlist_id}_user_{user_id}")
    logger.info(f"Invalidated cache for playlist {playlist_id}")
    logger.info(f'Playlist {playlist_id} deleted successfully')

    response = jsonify({
        "message": "Playlist deleted successfully",
        "_links": {
            "all_playlists": url_for('app_views.list_playlists', _external=True),
            "create_playlist": url_for('app_views.create_playlist', _external=True)
        }
    })
    return response, 200


@app_views.route('/playlists/<string:playlist_id>', methods=['GET'], strict_slashes=False)
def get_playlist(playlist_id: str) -> str:
    """Retrieve a playlist by ID"""

    # Get current user ID (if authenticated)
    current_user_id = session.get('user_id')

    # Check if the playlist is cached
    if current_user_id:
        cache_key = f"playlist_{playlist_id}_user_{current_user_id}"
    else:
        cache_key = f"playlist_{playlist_id}"
    cached_playlist = current_app.cache.get(cache_key)
    
    if cached_playlist:
        logger.info(f"Serving cached playlist {playlist_id}.")
        return jsonify(cached_playlist), 200

    # Fetch the playlist from the database
    playlist = storage.get(Playlist, playlist_id)
    if not playlist:
        logger.error(f'Playlist {playlist_id} not found')
        return jsonify({"error": "Playlist not found"}), 404

    # Prepare playlist details, including associated music metadata
    playlist_data = {
        "playlist": {
            "id": playlist.id,
            "name": playlist.name,
            "description": playlist.description,
            "music": [
                {
                    "id": music.id,
                    "title": music.title,
                    "duration": f"{music.duration // 60}:{music.duration % 60:02d}",
                    "artist": storage.get(Artist, music.artist_id).name if music.artist_id else "Unknown",
                    "album": storage.get(Album, music.album_id).title if music.album_id else "Unknown",
                    "fileUrl": music.file_url
                } for music in playlist.music
            ],
            "_links": {
                "self": url_for('app_views.get_playlist', playlist_id=playlist_id, _external=True),
                "all_playlists": url_for('app_views.list_playlists', _external=True)
            }
        }
    }

    # Add delete and update links only if the user is authenticated and owns the playlist
    if current_user_id and playlist.user_id == current_user_id:
        playlist_data["playlist"]["_links"].update({
            "delete": url_for('app_views.delete_playlist', playlist_id=playlist.id, _external=True),
            "update": url_for('app_views.update_playlist', playlist_id=playlist.id, _external=True)
        })

    for music in playlist_data["playlist"]["music"]:
        music["_links"] = {
            "self": url_for('app_views.get_music_metadata', music_id=music["id"], _external=True),
            "stream": url_for('app_views.stream_music', music_id=music["id"], _external=True)
        }

    # Cache the playlist response
    response = playlist_data
    current_app.cache.set(cache_key, response, timeout=3600)
    
    logger.info(f'Playlist {playlist_id} retrieved and cached successfully')
    return jsonify(response), 200


@app_views.route('/playlists', methods=['GET'], strict_slashes=False)
def list_playlists() -> str:
    """Retrieve a list of playlists with optional pagination"""
    
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    # Get current user ID (if authenticated)
    current_user_id = session.get('user_id')

    if current_user_id:
        cache_key = f"all_playlists_page_{page}_limit_{limit}_user_{current_user_id}"
    else:
        cache_key = f"all_playlists_page_{page}_limit_{limit}"
    cached_playlists = current_app.cache.get(cache_key)
    
    if cached_playlists:
        logger.info(f"Serving cached playlist list (page {page}, limit {limit}).")
        return jsonify(cached_playlists), 200
    
    # Retrieve all playlists
    playlists = storage.all(Playlist)
    
    # Pagination
    total_count = len(playlists)
    start_index = (page - 1) * limit
    end_index = page * limit
    playlist_subset = playlists[start_index:end_index]

    # Prepare the list of playlists with their metadata
    playlist_data = []
    for playlist in playlist_subset:
        playlist_info = {
            "id": playlist.id,
            "name": playlist.name,
            "music_count": len(playlist.music),
            "_links": {
                "self": url_for('app_views.get_playlist', playlist_id=playlist.id, _external=True),
            }
        }
        
        # Add delete and update links only if the user is authenticated and owns the playlist
        if current_user_id and playlist.user_id == current_user_id:
            playlist_info["_links"].update({
                "delete": url_for('app_views.delete_playlist', playlist_id=playlist.id, _external=True),
                "update": url_for('app_views.update_playlist', playlist_id=playlist.id, _external=True)
            })
        
        playlist_data.append(playlist_info)
    
    response_data = {
        "playlists": playlist_data,
        "total_count": total_count,
        "page": page,
        "limit": limit,
        "_links": {
            "self": url_for('app_views.list_playlists', page=page, limit=limit, _external=True),
            "next": url_for('app_views.list_playlists', page=page+1, limit=limit, _external=True) if end_index < total_count else None,
            "prev": url_for('app_views.list_playlists', page=page-1, limit=limit, _external=True) if page > 1 else None,
            "first": url_for('app_views.list_playlists', page=1, limit=limit, _external=True),
            "last": url_for('app_views.list_playlists', page=-(total_count // -limit), limit=limit, _external=True),
        }
    }
    
    # Add create_playlist link only for authenticated users
    if current_user_id:
        response_data["_links"]["create_playlist"] = url_for('app_views.create_playlist', _external=True)
    
    # Cache the response for pagination
    current_app.cache.set(cache_key, response_data, timeout=3600)
    
    logger.info(f'Playlist list retrieved successfully (page {page}, limit {limit}) and cached.')
    return jsonify(response_data), 200


def invalidate_all_playlists_cache():
    """Invalidate all cache entries related to playlists."""
    cache = current_app.cache
    pattern = "flask_cache_all_playlists_*"

    # Get all keys matching the pattern
    keys_to_delete = [key.decode('utf-8') for key in cache.cache._read_client.keys(pattern)]

    if keys_to_delete:
        # Adjust the keys for deletion by removing any prefix if necessary
        adjusted_keys = [key.replace('flask_cache_', '', 1) for key in keys_to_delete]
        cache.delete_many(*adjusted_keys)
        logger.info(f"Invalidated {len(adjusted_keys)} cache entries for all playlists")
    else:
        logger.info("No cache entries found to invalidate for all playlists")
