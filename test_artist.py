#!/usr/bin/python3
from models.artist import Artist

# Create a new Artist instance
artist1 = Artist()
artist1.name = "Jay Z"
artist1.bio = "Blues."
artist1.profile_picture_url = "https://example.com/beyonce.jpg"
artist1.user_id = '5f7b28c9-ab65-40a0-bc8a-9ad271b86d2a'

# Save the artist to the database
artist1.save()

# Print the artist object
print(artist1)


