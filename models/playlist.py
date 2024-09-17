#!/usr/bin/env python3
"""
Playlist class
"""
from sqlalchemy import Column, String, Text, ForeignKey, Table, Integer
from sqlalchemy.orm import relationship
from models.base_model import BaseModel, Base
from models.music import Music
from models.user import User
from models import storage
from typing import List, Dict, Any, Type


# Association table for Playlist and Music with cascading on update and delete
playlist_music = Table(
    'PlaylistMusic',
    Base.metadata,
    Column('order', Integer, primary_key=True, autoincrement=True),
    Column('playlist_id', String(60), ForeignKey('Playlists.id',
           onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
    Column('music_id', String(60), ForeignKey('Music.id',
           onupdate='CASCADE', ondelete='CASCADE'), nullable=False)
)


class Playlist(BaseModel, Base):
    """Representation of a Playlist class"""
    __tablename__ = 'Playlists'

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(String(60), ForeignKey('Users.id', ondelete='CASCADE'),
                     nullable=False)

    # Relationship with Music through PlaylistMusic
    music = relationship('Music', secondary=playlist_music, backref='Playlists')

    def __init__(self, *args: List[Any], **kwargs: Dict[str, Any]) -> None:
        """Initializes Playlist"""
        super().__init__(*args, **kwargs)

    def add_music(self,
                  cls: Type[BaseModel],
                  cls_id: str, music: Music
                  ) -> None:
        """Add music to the playlist"""
        playlist = storage.get(cls, cls_id)
        if playlist is None:
            raise ValueError(f"Playlist with id {cls_id} not found.")
        playlist.music.append(music)
        playlist.save()

    def remove_music(self,
                     cls: Type[BaseModel],
                     cls_id: str, music: Music
                     ) -> None:
        """Remove music from the playlist"""
        playlist = storage.get(cls, cls_id)
        if playlist is None:
            raise ValueError(f"Playlist with id {cls_id} not found.")
        if music not in playlist.music:
            raise ValueError(f"Music not found in the playlist.")
        playlist.music.remove(music)
        playlist.save()
