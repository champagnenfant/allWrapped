import os

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Music Wrapped API")

# À restreindre à l'URL de ton frontend une fois déployé
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

API_TOKEN = os.getenv("API_TOKEN", "dev-token-change-me")


def verify_token(authorization: str = Header(default="")):
    token = authorization.removeprefix("Bearer ").strip()
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/plays", response_model=schemas.PlayOut, status_code=201)
def create_play(
    play: schemas.PlayCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_token),
):
    # Dédoublonnage simple : si une écoute identique (même titre/artiste/
    # plateforme) existe déjà dans les 3 dernières minutes, on l'ignore
    # plutôt que de la dupliquer (utile car le sensor poll toutes les 5s).
    recent_duplicate = (
        db.query(models.Play)
        .filter(
            models.Play.title == play.title,
            models.Play.artist == play.artist,
            models.Play.platform == play.platform,
            models.Play.played_at >= play.played_at.replace(microsecond=0),
        )
        .first()
    )
    if recent_duplicate:
        return recent_duplicate

    db_play = models.Play(**play.model_dump())
    db.add(db_play)
    db.commit()
    db.refresh(db_play)
    return db_play


@app.get("/api/plays", response_model=list[schemas.PlayOut])
def list_plays(
    limit: int = 50,
    db: Session = Depends(get_db),
    _: None = Depends(verify_token),
):
    return (
        db.query(models.Play)
        .order_by(models.Play.played_at.desc())
        .limit(limit)
        .all()
    )


@app.get("/api/stats/top-artists")
def top_artists(
    limit: int = 10,
    db: Session = Depends(get_db),
    _: None = Depends(verify_token),
):
    results = (
        db.query(models.Play.artist, func.count(models.Play.id).label("play_count"))
        .filter(models.Play.artist.isnot(None))
        .group_by(models.Play.artist)
        .order_by(func.count(models.Play.id).desc())
        .limit(limit)
        .all()
    )
    return [{"artist": artist, "play_count": count} for artist, count in results]
