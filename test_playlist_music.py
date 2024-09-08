#!/usr/bin/env python3
from models.playlist import Playlist
from models.music import Music
from models import storage  # Ensure this import path is correct

playlist = Playlist()

# IDs of existing playlists and music
playlist_id_1 = '068b2bad-ad39-495e-acdb-f5550484444b'
playlist_id_2 = '4b9cb69d-cbeb-4143-ae09-59acea221534'
music_id_1 = '93fdae4b-d883-46dc-8c42-909df903b02a'
music_id_2 = '56d76968-0eb4-40ce-b4bb-355205086ac5'
music_id_3 = '7b203acb-ade7-4a24-87a8-d11f389f91f6'
music_id_4 = 'b947ec8b-7759-4a53-a618-44e7ce83bdc2'
music_id_5 = 'babbf717-c1cc-4085-9e3e-efb8853db289'

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

