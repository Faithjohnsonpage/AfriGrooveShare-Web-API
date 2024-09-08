#!/usr/bin/python3
from models.album import Album
from datetime import date

# Create a new Album instance
my_album = Album()
my_album.title = "Greatest Hits"
my_album.artist_id = "0b926bab-23bc-43bd-84ce-73174cf38a56"
my_album.release_date = date(2024, 9, 1)
my_album.cover_image_url = "https://example.com/cover.jpg"

# Save the album to the database
my_album.save()

# Print the album object
print(my_album)
