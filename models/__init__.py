#!/usr/bin/env python3
"""
Initialize the models package
"""
from models.engine.db import DB


storage = DB()
storage.reload()
