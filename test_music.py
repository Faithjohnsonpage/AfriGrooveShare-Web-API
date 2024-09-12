#!/usr/bin/env python3
"""
Test for Music class
"""
from models.music import Music

# List of track titles
track_titles = [
    "Track 1",
]

# Common IDs for artist, album, and genre
artist_id = "375e26e0-42c1-4d61-898e-18ee55c20ed3"
album_id = "66b88f87-8f50-40fc-8fd1-389a87326917"
genre_id = "737a8ac6-ce58-40b0-9681-8cfc3a075aec"

# Loop to create and save music tracks
for i, title in enumerate(track_titles, start=6):
    music = Music()
    music.title = title
    music.artist_id = artist_id
    music.album_id = album_id
    music.genre_id = genre_id
    music.file_url = f"https://example.com/music/track_{i}.mp3"
    music.duration = 210  # duration in seconds
    music.release_date = "2024-09-04"  # Example date

    # Save the music to the database
    music.save()

    # Print the music object
    print(music)

