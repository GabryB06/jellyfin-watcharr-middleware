# Jellyfin Watcharr middleware

Mark on Watcharr finished episodes on Jellyfin via webhook

---

> [!TIP]
> Watcharr has a built-in feature similar to the one provided by this middleware, but requires to have a Jellyfin linked Watcharr account, thing that some users might not really like (as there is no alternative way to login, for example if the Jellyfin server goes down)

## Tested versions

Tested against Jellyfin 12.4 and Watcharr 4.3.0

## Setup

Make sure to rename the files `.env.example` and `credentials.example.json` to `.env` and `credentials.json`

Please expose this container only to a Docker internal network accessed only by Jellyfin and Watcharr (example [compose file](docker-compose.yml) has this configuration applied).

Webhook is received on port 8000

### Webhook (Jellyfin admin side)

1. install the Webhook plugin and restart your Jellyfin instance
2. in the webhook plugin configuration add a new entry and put:

> - Webhook Url: `http://middleware:8000` (or how you named the middleware container in [docker-compose.yml](docker-compose.yml))
> - Status: Enable
> - Notification Type: Playback stop
> - User filter: (here select the users who this middleware will work for (make sure they are mapped in [credentials.json](credentials.example.json)))
> - Item Type: (you can leave it as default)
> - mark `Send All Properties (ignores template)`

### [.env](.env.example)

Make sure Jellyfin and Watcharr hosts are configured correctly and create a Jellyfin API key from the admin dashboard (`http://{your_jellyfin_instance}/web/#/dashboard/keys`) and put it in `JELLYFIN_API_KEY` (it's needed to lookup TV shows episodes' The Movie Database (TMDB) ID)

### [credentials.json](credentials.example.json)

Fill it with the list of the Watcharr users (and password) who will use the middleware and map it to their Jellyfin username.

> [!CAUTION]
> Watcharr users' credentials are saved in plaintext, this is currently the only way to authenticate to the server as there is no support for API keys. Be aware of this potential risk.
