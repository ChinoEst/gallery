from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    token: str


class ArtistCreate(BaseModel):
    name: str
    url: str
    platform: str

class ArtistResponse(BaseModel):
    id: int
    name: str
    url: str
    platform: str
    created_at: datetime

    class Config:
        from_attributes = True


class TagResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ImageResponse(BaseModel):
    id: int
    artist_id: int
    original_url: str
    thumbnail_url: Optional[str]
    is_downloaded: bool
    local_path: Optional[str]
    created_at: datetime
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True


class DownloadRequest(BaseModel):
    image_ids: List[int]