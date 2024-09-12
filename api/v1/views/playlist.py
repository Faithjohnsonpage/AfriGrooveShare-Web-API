#!/usr/bin/env python3
from flask import jsonify, request, session
from models import storage
from models.playlist import Playlist
from models.music import Music
from models.artist import Artist
from models.album import Album
from api.v1.views import app_views


@app_views.route('/playlist/create', methods=['POST'], strict_slashes=False)
def create_playlist():
    """Create a new playlist"""
    if 'user_id' not in session:
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    name = request.form.get('name')
    description = request.form.get('description')

    if not name:
        return jsonify({"error": "Missing name"}), 400

    playlist = Playlist()
    playlist.name = name
    playlist.description = description
    playlist.user_id = user_id
    storage.new(playlist)
    storage.save()

    return jsonify({"message": "Playlist created successfully", "playlistId": playlist.id}), 201


@app_views.route('/playlists/<playlist_id>', methods=['POST'], strict_slashes=False)
def update_playlist(playlist_id):
    """Update a playlist, either by editing or adding music"""
    if 'user_id' not in session:
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    playlist = storage.get(Playlist, playlist_id)
    if not playlist:
        return jsonify({"error": "Playlist not found"}), 404

    # Ensure the user is the owner of the playlist
    if playlist.user_id != user_id:
        return jsonify({"error": "Unauthorized to delete this playlist"}), 403

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
        return jsonify({"message": "Playlist updated successfully"}), 200

    # Handle adding music to the playlist
    elif action == 'add_music':
        music_ids = request.form.getlist('musicIds')

        if not music_ids:
            return jsonify({"error": "No music provided"}), 400

        for music_id in music_ids:
            music = storage.get(Music, music_id)
            if music:
                try:
                    playlist.add_music(Playlist, playlist_id, music)
                except ValueError as e:
                    return jsonify({"error": str(e)}), 400
            else:
                return jsonify({"error": f"Music with id {music_id} not found"}), 404

        return jsonify({"message": "Music added to playlist successfully"}), 200

    # Handle removing music from the playlist
    elif action == 'remove_music':
        music_ids = request.form.getlist('musicIds')

        if not music_ids:
            return jsonify({"error": "No music provided"}), 400

        for music_id in music_ids:
            music = storage.get(Music, music_id)
            if music:
                try:
                    playlist.remove_music(Playlist, playlist_id, music)
                except ValueError as e:
                    return jsonify({"error": str(e)}), 400
            else:
                return jsonify({"error": f"Music with id {music_id} not found"}), 404

        return jsonify({"message": "Music removed from playlist successfully"}), 200

    return jsonify({"error": "Invalid action provided"}), 400


@app_views.route('/playlists/<playlist_id>', methods=['DELETE'], strict_slashes=False)
def delete_playlist(playlist_id):
    """Delete a playlist"""
    # Check if the user is logged in
    if 'user_id' not in session:
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Retrieve the playlist
    playlist = storage.get(Playlist, playlist_id)
    if not playlist:
        return jsonify({"error": "Playlist not found"}), 404

    # Ensure the user is the owner of the playlist
    if playlist.user_id != user_id:
        return jsonify({"error": "Unauthorized to delete this playlist"}), 403

    # Delete the playlist
    storage.delete(playlist)
    storage.save()

    return jsonify({"message": "Playlist deleted successfully"}), 200


@app_views.route('/playlists/<playlist_id>', methods=['GET'], strict_slashes=False)
def get_playlist(playlist_id):
    """Retrieve a playlist by ID"""
    playlist = storage.get(Playlist, playlist_id)
    if not playlist:
        return jsonify({"error": "Playlist not found"}), 404

    # Return playlist details including associated music
    return jsonify({
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
            ]
        }
    }), 200