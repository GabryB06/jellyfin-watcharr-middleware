import requests
import os

host = os.environ["JELLYFIN_HOST"]
api_key = os.environ["JELLYFIN_API_KEY"]

headers = {'Authorization': f'MediaBrowser Token="{api_key}"'}

def get_tmdb_id(content_id: str, user_id: str):
    """Ottiene da Jellyfin l'ID TMDB del contenuto richiesto

    Args:
        content_id: ID contenuto elemento memorizzato in Jellyfin
        user_id: ID utente per conto di cui viene effettuata la richiesta
    
    Returns:
        [0] ID TheMovieDB, [1] response code o None se 200
    """
    req = requests.get(url=f"{host}/Users/{user_id}/Items/{content_id}", headers=headers)
    if req.status_code == 200:
        data = req.json()
        return(data["ProviderIds"]["Tmdb"], None)
    else:
        return (None, req.status_code)