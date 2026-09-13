from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
import json
import logging

import jellyfin_api_client as jellyfin
import watcharr_client as watcharr

app = FastAPI()
logger = logging.getLogger(__name__)

class Webhook(BaseModel):
    NotificationType: str               # Evento che ha causato l'invio del webhook (dovrebbe essere sempre PlaybackStop)
    ItemType: str                       # Solamente Episode e Movie vengono gestiti (Watcharr gestisce solamente serie TV e film)
    SeriesId: str | None = None         # Solo per serie TV (ItemType = Episode)
    SeasonNumber: int | None = None     # Solo per serie TV (ItemType = Episode)
    EpisodeNumber: int | None = None    # Solo per serie TV (ItemType = Episode)
    Provider_tmdb: int | None = None    # Solo per film (ItemType = Movie), per serie deve essere recuperato via API con SeriesId
    PlayedToCompletion: bool            # Se il media è stato completato oppure è no (visto che l'evento viene inviato alla fine della riproduzione che può anche essere interrotta)
    UserId: str                         # ID utente Jellyfin (utile per API)
    NotificationUsername: str           # Nome utente Jellyfin (utile per incrociare con Watcharr in setup multi utente)

try:
    with open("credentials.json", "r") as file:
        data = json.load(file)
except FileNotFoundError:
    logger.error("User map file not found")
    raise

def get_credentials(NotificationUsername: str):
    """Ottiene le credenziali Watcharr dell'utente dal file JSON
    Args:
        NotificationUsername: Nome dell'utente Jellyfin da cercare (jellyfin_user)
    Returns:
        nome utente Watcharr (watcharr_user) e password (watcharr_pass)
    """
    for i in data["users"]:
        if i["jellyfin_user"] == NotificationUsername:
            return(i["watcharr_user"],i["watcharr_pass"])
    return None

@app.post("/")
async def webhook(request: Request):

    # Parse JSON manuale per bypassare `Content-Type: text/plain` invece di `Content-Type: application/json` nella richiesta
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Payload non è JSON valido")

    try:
        webhook = Webhook(**payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    # Evita di processare tipi di contenuto non gestiti
    if webhook.ItemType != "Episode" and webhook.ItemType != "Movie":
        return {"error": f"ItemType sconosciuto {webhook.ItemType}"}
    
    # Evita di processare eventi non gestiti ed eventi di interruzione senza completamento dell'elemento
    if webhook.NotificationType != "PlaybackStop" or webhook.PlayedToCompletion != True:
        return {"warn": "condizioni riproduzione fallite"}

    # Evita di processare utenti non presenti nel file di configurazione
    credentials = get_credentials(webhook.NotificationUsername)
    if credentials is None:
        return {"warn": "utente sconosciuto"}

    # Effettua il login in Watcharr ed ottiene la lista degli elementi memorizzati
    login = watcharr.do_login(credentials)
    if login == 403:
        return JSONResponse(status_code=403, content={"error": "credenziali watcharr non valide"})
    elif login is not None:
        return JSONResponse(status_code=login, content={"error": "Watcharr error"})
    
    watcharr_list = watcharr.get_list()

    # Verifica se è film o serie TV
    if webhook.ItemType == "Episode":

        tmdbID = jellyfin.get_tmdb_id(webhook.SeriesId, webhook.UserId)
        if tmdbID[1] == 401:
            return JSONResponse(status_code=401, content={"error": "chiave API Jellyfin non valida"})
        elif tmdbID[1] is not None:
            return JSONResponse(status_code=tmdbID[1], content={"error": "Jellyfin error"})
        
        # Se è una serie TV la aggiunge alla lista (se assente) e segna l'episodio come finito
        media_id = watcharr.is_item_in_list(tmdbID[0], watcharr_list)
        if media_id is None:
            media_id = watcharr.add_series_to_list(tmdbID[0])
        watcharr.mark_episode(media_id, webhook.SeasonNumber, webhook.EpisodeNumber)
        return "ok"
    else:
        tmdbID = webhook.Provider_tmdb
        # Se è un film lo aggiunge alla lista (se assente) e lo segna come finito
        media_id = watcharr.is_item_in_list(tmdbID, watcharr_list)
        if media_id is None:
            media_id = watcharr.add_movie_to_list(tmdbID)
        watcharr.mark_movie(media_id)
        return "ok"