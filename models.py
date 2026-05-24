from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)

    #back_populates:update both image.user and user.images
    images = relationship("Image", back_populates="user")

class Artist(Base):
    __tablename__ = "artists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    url = Column(String, unique=True)
    platform = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    images = relationship("Image", back_populates="artist")

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    #connect base on user.id
    user_id = Column(Integer, ForeignKey("users.id"))
    artist_id = Column(Integer, ForeignKey("artists.id"))
    filename = Column(String, nullable=True)
    original_url = Column(String)
    thumbnail_url = Column(String, nullable=True)
    is_downloaded = Column(Boolean, default=False)
    local_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    #one to many relationship with User and Artist
    user = relationship("User", back_populates="images")
    artist = relationship("Artist", back_populates="images")
    
    #many to many relationship with Tag through ImageTag
    tags = relationship("Tag", secondary="image_tags", back_populates="images")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    images = relationship("Image", secondary="image_tags", back_populates="tags")

class ImageTag(Base):
    __tablename__ = "image_tags"

    image_id = Column(Integer, ForeignKey("images.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)