"""
Music Tracker - Sensor Windows
--------------------------------
Capte en continu ce qui est en train de jouer sur le PC (Apple Music,
onglets navigateur YouTube/YouTube Music/SoundCloud, Spotify desktop, etc.)
via l'API Windows SMTC (System Media Transport Controls) et envoie chaque
nouvelle écoute détectée à ton backend.

Pré-requis:
    pip install winsdk requests

Lancement:
    python music_tracker_sensor.py

Pour le faire tourner en fond au démarrage de Windows, voir la fin du fichier
(section "AUTOSTART").
"""

import asyncio
import os
import time
import requests
from datetime import datetime, timezone

from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
)
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
)

# ---------------------------------------------------------------------------
# CONFIG - à adapter
# ---------------------------------------------------------------------------
BACKEND_URL = os.getenv("SENSOR_BACKEND_URL", "http://localhost:8000/api/plays")
AUTH_TOKEN = os.getenv("SENSOR_API_TOKEN", "dev-token-change-me")
POLL_INTERVAL_SECONDS = 5  # fréquence de vérification

# Mapping approximatif app id Windows -> nom de plateforme lisible.
# À enrichir au fil de tes tests : lance le script, regarde les
# source_app_user_model_id qui s'affichent dans la console, et complète.
APP_ID_TO_PLATFORM = {
    "AppleInc.AppleMusicWin_nzyj5cx40ttqa!App": "apple_music",
    "Microsoft.MicrosoftEdge_8wekyb3d8bbwe!MSEDGE": "browser_edge",
    "Google Chrome": "browser_chrome",
    "chrome.exe": "browser_chrome",
    "msedge.exe": "browser_edge",
    "firefox.exe": "browser_firefox",
    "Spotify.exe": "spotify",
}


def guess_platform(app_id: str, title: str, artist: str) -> str:
    """Devine la plateforme source. Pour les navigateurs, on ne peut pas
    savoir directement si l'onglet actif est YouTube ou SoundCloud via
    l'API SMTC seule (elle ne donne pas l'URL) -- il faudra affiner ça
    plus tard, potentiellement avec une petite extension navigateur qui
    complète l'info, ou en se basant sur des heuristiques (présence
    d'un artiste structuré = plutôt Apple Music/Spotify, etc.)."""
    return APP_ID_TO_PLATFORM.get(app_id, app_id)


async def get_active_sessions():
    manager = await MediaManager.request_async()
    return manager.get_sessions()


async def poll_once(last_seen: dict):
    """Vérifie toutes les sessions média actives, envoie un event pour
    chaque nouvelle piste détectée en train de jouer."""
    sessions = await get_active_sessions()

    for session in sessions:
        try:
            playback_info = session.get_playback_info()
            if playback_info.playback_status != PlaybackStatus.PLAYING:
                continue

            props = await session.try_get_media_properties_async()
            if not props or not props.title:
                continue

            app_id = session.source_app_user_model_id
            key = f"{app_id}|{props.title}|{props.artist}"

            # Nouvelle piste (différente de la dernière vue pour cette app) ?
            if last_seen.get(app_id) == key:
                continue
            last_seen[app_id] = key

            platform = guess_platform(app_id, props.title, props.artist)
            event = {
                "title": props.title,
                "artist": props.artist,
                "album": props.album_title,
                "platform": platform,
                "source_app_id": app_id,
                "played_at": datetime.now(timezone.utc).isoformat(),
            }

            print(f"[{event['played_at']}] {platform}: {props.artist} - {props.title}")
            send_event(event)

        except Exception as e:
            print(f"Erreur lecture session ({session.source_app_user_model_id}): {e}")


def send_event(event: dict):
    try:
        requests.post(
            BACKEND_URL,
            json=event,
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            timeout=5,
        )
    except requests.RequestException as e:
        # TODO: mettre en file d'attente locale si le backend est down,
        # pour ne pas perdre les events (ex: fichier local + retry).
        print(f"Échec envoi au backend: {e}")


async def main_loop():
    last_seen = {}
    print("Music Tracker Sensor démarré. Ctrl+C pour arrêter.")
    while True:
        await poll_once(last_seen)
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\nArrêt du sensor.")

# ---------------------------------------------------------------------------
# AUTOSTART (à faire une fois que le script fonctionne bien manuellement)
# ---------------------------------------------------------------------------
# Option simple : raccourci dans le dossier de démarrage Windows
#   1. Win+R -> shell:startup
#   2. Créer un raccourci vers : pythonw.exe C:\chemin\music_tracker_sensor.py
#      (pythonw.exe = pas de fenêtre console qui reste ouverte)
#
# Option plus robuste : tâche planifiée (Task Scheduler)
#   - Déclencheur : à l'ouverture de session
#   - Action : lancer pythonw.exe avec le script en argument
#   - Avantage : redémarre automatiquement en cas de crash si tu coches
#     l'option "Redémarrer la tâche en cas d'échec"
