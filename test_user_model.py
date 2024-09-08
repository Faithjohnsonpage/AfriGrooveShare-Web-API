#!/usr/bin/env python3
"""
Test script for the User class with password hashing
"""
from models.user import User
from models import storage  # Assuming storage is your database engine or session manager

def test_user():
    # Create a new User instance
    new_user = User()
    new_user.username = "testuser"
    new_user.email = "testuser@example.com"
    new_user.password = "securepassword"  # This will be hashed

    # Save the user to the database
    new_user.save()

    # Retrieve the user from the database
    fetched_user = storage.get(User, new_user.id)
    
    # Verify the password
    is_password_correct = fetched_user.verify_password("securepassword")

    # Print results
    print(f"User created: {new_user}")
    print(f"Password verification result: {is_password_correct}")

if __name__ == "__main__":
    test_user()
