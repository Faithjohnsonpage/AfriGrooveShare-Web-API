#!/usr/bin/env python3
"""
Test for Music class
"""
from models.music import Music

# Assuming you already have an artist, album, and genre in the database

# Create a new Music instance
my_music1 = Music()
my_music1.title = "Track 7"
my_music1.artist_id = "0b926bab-23bc-43bd-84ce-73174cf38a56"
my_music1.album_id = "80a86ee2-d7a2-485d-b70c-9f22e9afbef7"
my_music1.genre_id = "737a8ac6-ce58-40b0-9681-8cfc3a075aec"
my_music1.file_url = "https://example.com/music/track_7.mp3"
my_music1.duration = 210  # duration in seconds
my_music1.release_date = "2024-09-04"  # Example date

# Save the music to the database
my_music1.save()

# Print the music object
print(my_music1)
