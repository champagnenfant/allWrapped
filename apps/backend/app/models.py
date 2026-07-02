from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from .database import Base


class Play(Base):
    """Une écoute individuelle, telle que remontée par un sensor
    (Windows SMTC, API Spotify, API Deezer, etc.)"""

    __tablename__ = "plays"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=True)
    album = Column(String, nullable=True)
    platform = Column(String, nullable=False, index=True)  # apple_music, spotify, deezer, browser_edge...
    source_app_id = Column(String, nullable=True)
    played_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Dédoublonnage grossier : même titre+artiste+plateforme dans une
    # fenêtre de quelques minutes = probablement le même event renvoyé
    # deux fois par le sensor (polling qui recouvre). On affinera la
    # logique de dédup dans le CRUD plutôt qu'au niveau du schéma.
