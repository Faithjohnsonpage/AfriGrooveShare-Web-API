#!/usr/bin/env python3
"""
Album class
"""
from sqlalchemy import Column, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from models.base_model import BaseModel, Base
from models.artist import Artist
from typing import List, Dict, Any


class Album(BaseModel, Base):
    """Representation of an Album class"""

    __tablename__ = 'Albums'
 
    title = Column(String(255), nullable=False)
    artist_id = Column(String(60), ForeignKey('Artists.id'), nullable=False)
    release_date = Column(Date)
    cover_image_url = Column(Text)
 
    def __init__(self, *args: List[Any], **kwargs: Dict[str, Any]) -> None:
        """Initializes Album"""
        super().__init__(*args, **kwargs)
