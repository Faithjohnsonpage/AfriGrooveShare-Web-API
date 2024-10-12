#!/usr/bin/env python3
"""
Script to create an instance of Admin and set the user_id.
"""
from models.admin import Admin


admin = Admin()
admin.user_id = '1bad5a0f-7ba4-4b99-9bab-dfae685d3012'
admin.save()
