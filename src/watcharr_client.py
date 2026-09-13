import requests
import os

host = os.environ["WATCHARR_HOST"]

headers = {}

def do_login(credentials: dict):
    """Esegue il login in Watcharr e imposta l'header di autenticazione

    Args:
        credentials: dizionario con [0] username e [1] password
    Returns:
        response code se != 200, altrimenti None
    """
    auth = {"username":credentials[0], "password":credentials[1]}
    req = requests.post(url=f"{host}/api/auth", json=auth)
    if req.status_code == 200:
        data = req.json()
        token = data["token"]
        global headers
        headers = {"authorization": f"{token}"}
        return None
    else:
        return req.status_code

def get_list():
    """Ottiene da Watcharr l'elenco dei media presenti nella lista
    
    Returns:
        oggetto JSON contenente l'intera lista
    """
    req = requests.get(url=f"{host}/api/watched", headers=headers)
    data = req.json()
    return data

def is_item_in_list(tmdbID: int, data: dict):
    """Verifica che l'elemento sia già presente nella lista

    Args:
        tmdbID: ID TheMovieDB da cercare
        data: oggetto JSON dentro cui cercare l'ID
    
    Returns:
        ID Watcharr elemento se trovato, altrimenti Null
    """
    for i in data:
        if i["content"]["tmdbId"] == int(tmdbID):
            return i["id"]
    return None

def add_series_to_list(tmdbID: int):
    """Aggiunge in Watcharr la serie TV alla lista
    
    Args:
        tmdbID: ID TheMovieDB da aggiungere
    
    Returns:
        ID Watcharr elemento appena aggiunto
    """
    req = requests.post(url=f"{host}/api/watched", headers=headers, json={"contentType": "tv",
                                                                          "status": "WATCHING",
                                                                          "tmdbId":int(tmdbID)
                                                                          })
    data = req.json()
    return(data["id"])

def mark_episode(series_id: int, season: int, episode: int):
    """Contrassegna in Watcharr l'episodio come completato
    
    Args:
        series_id: ID Watcharr serie
        season: numero stagione
        episode: numero episodio
    """
    requests.post(url=f"{host}/api/watched/episode", headers=headers, json={"watchedId": series_id,
                                                                            "seasonNumber": season,
                                                                            "episodeNumber": episode,
                                                                            "status": "FINISHED"
                                                                            })

def add_movie_to_list(tmdbID: int):
    """Aggiunge in Watcharr il film alla lista
        
    Args:
        tmdbID: ID TheMovieDB da aggiungere
        
    Returns:
        ID Watcharr elemento appena aggiunto
    """
    req = requests.post(url=f"{host}/api/watched", headers=headers, json={"contentType": "movie",
                                                                          "status": "FINISHED",
                                                                          "tmdbId": int(tmdbID)
                                                                          })
    data = req.json()
    return(data["id"])

def mark_movie(movie_id: int):
    """Contrassegna in Watcharr il film come completato
        
    Args:
        movie_id: ID Watcharr film
    """
    requests.put(url=f"{host}/api/watched/{str(movie_id)}", headers=headers, json={"status": "FINISHED"})