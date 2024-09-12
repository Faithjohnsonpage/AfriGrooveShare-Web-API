#!/usr/bin/env python3
from models.playlist import Playlist
from models.music import Music
from models import storage  # Ensure this import path is correct

playlist = Playlist()

# IDs of existing playlists and music
playlist_id_1 = '068b2bad-ad39-495e-acdb-f5550484444b'
playlist_id_2 = '4b9cb69d-cbeb-4143-ae09-59acea221534'
music_id_1 = '33ccc54e-04fb-4a5e-afe9-fceb2d1c00a2'
music_id_2 = '4c3bf4a5-ed88-42ae-aebd-36bdd60e8a29'
music_id_3 = '72e00bda-e76d-4853-8bc6-7048d9849918'
music_id_4 = '981289ef-3f9d-490b-bc6b-7c2b3d6f996d'
music_id_5 = 'f3721bb4-7458-4f83-8ba5-087f7176f9a6'

# Fetch the existing playlists and music from the database
playlist_1 = storage.get(Playlist, playlist_id_1)
playlist_2 = storage.get(Playlist, playlist_id_2)
music_1 = storage.get(Music, music_id_1)
music_2 = storage.get(Music, music_id_2)
music_3 = storage.get(Music, music_id_3)
music_4 = storage.get(Music, music_id_4)
music_5 = storage.get(Music, music_id_5)

# Check if playlists and music were found
if playlist_1 is None:
    print(f"Playlist with ID {playlist_id_1} not found.")
if playlist_2 is None:
    print(f"Playlist with ID {playlist_id_2} not found.")
if music_1 is None:
    print(f"Music with ID {music_id_1} not found.")
if music_2 is None:
    print(f"Music with ID {music_id_2} not found.")
if music_3 is None:
    print(f"Music with ID {music_id_3} not found.")
if music_4 is None:
    print(f"Music with ID {music_id_4} not found.")
if music_5 is None:
    print(f"Music with ID {music_id_5} not found.")

# Add music to the playlists if they were found
if playlist_1 and music_1 and music_2:
    playlist.add_music(Playlist, playlist_id_1, music_1)
    playlist.add_music(Playlist, playlist_id_1, music_2)
if playlist_2 and music_3 and music_4 and music_5:
    playlist.add_music(Playlist, playlist_id_2, music_3)
    playlist.add_music(Playlist, playlist_id_2, music_4)
    playlist.add_music(Playlist, playlist_id_2, music_5)

# Print the updated playlists
print("Updated Playlist 1")
print("Updated Playlist 2")

