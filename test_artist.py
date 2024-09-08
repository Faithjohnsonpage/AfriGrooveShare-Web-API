#!/usr/bin/python3
from models.artist import Artist

# Create a new Artist instance
artist1 = Artist()
artist1.name = "Lionel Richie"
artist1.bio = "A renowned guitarist."
artist1.profile_picture_url = "https://example.com/lionel_richie.jpg"

# Save the artist to the database
artist1.save()

# Print the artist object
print(artist1)
