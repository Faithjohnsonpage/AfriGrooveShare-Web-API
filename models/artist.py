#!/usr/bin/env python3
"""
Artist class
"""
from sqlalchemy import Column, String, Text
from models.base_model import BaseModel, Base
from sqlalchemy.orm import relationship
from models.album import Album
from typing import List, Dict, Any


class Artist(BaseModel, Base):
    """Representation of an Artist class"""

    __tablename__ = 'Artists'
    
    name = Column(String(255), nullable=False)
    bio = Column(Text, nullable=True)
    profile_picture_url = Column(Text, nullable=True)

    # Establish a bidirectional relationship with Album
    albums = relationship('Album', backref='artist', cascade='all, delete-orphan')

    def __init__(self, *args: List[Any], **kwargs: Dict[str, Any]) -> None:
        """Initializes Artist"""
        super().__init__(*args, **kwargs)
