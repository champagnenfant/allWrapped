from datetime import datetime

from pydantic import BaseModel


class PlayCreate(BaseModel):
    title: str
    artist: str | None = None
    album: str | None = None
    platform: str
    source_app_id: str | None = None
    played_at: datetime


class PlayOut(PlayCreate):
    id: int

    class Config:
        from_attributes = True
