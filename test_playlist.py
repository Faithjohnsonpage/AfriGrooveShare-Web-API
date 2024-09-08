#!/usr/bin/env python3
from models.playlist import Playlist


# Create a new Playlist instance
my_playlist = Playlist()
my_playlist.name = "Laid-back Tunes"
my_playlist.description = "Perfect for when you need to take it easy and chill out."
my_playlist.user_id = "cc20a2ee-5302-476b-8a67-3319c23f2676"

# Save the playlist to the database
my_playlist.save()

# Print the playlist object
print(my_playlist)
