#!/usr/bin/env python3
"""
Music class
"""
import models
from sqlalchemy import Column, String, Text, Integer, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from models.base_model import BaseModel, Base
from models.artist import Artist
from models.genre import Genre
from models.album import Album
from typing import List, Dict, Any
import enum


class ReleaseType(enum.Enum):
    ALBUM = "ALBUM"
    SINGLE = "SINGLE"


class Music(BaseModel, Base):
    """Representation of a Music class"""
    __tablename__ = 'Music'
    title = Column(String(255), nullable=False)
    artist_id = Column(String(60), ForeignKey('Artists.id', ondelete='CASCADE'), nullable=False)
    album_id = Column(String(60), ForeignKey('Albums.id', ondelete='CASCADE'), nullable=True)
    genre_id = Column(String(60), ForeignKey('Genres.id'), nullable=False)
    file_url = Column(Text, nullable=False)
    duration = Column(Integer, nullable=False)
    release_date = Column(Date, nullable=True)
    cover_image_url = Column(Text)
    description = Column(Text, nullable=True)
    release_type = Column(Enum(ReleaseType), nullable=False)

    def __init__(self, *args: List[Any], **kwargs: Dict[str, Any]) -> None:
        """Initializes Music"""
        super().__init__(*args, **kwargs)
