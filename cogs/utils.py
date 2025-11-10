import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, YTDL_OPTIONS

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

async def search_youtube(query: str):
    """Busca un video en YouTube y devuelve URL + título."""
    info = ytdl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]
    return info["url"], info["title"]

async def get_spotify_tracks(url: str):
    """Convierte canciones de Spotify (track o playlist) en títulos buscables en YouTube."""
    tracks = []
    if "track" in url:
        data = sp.track(url)
        tracks.append(f"{data['artists'][0]['name']} {data['name']}")
    elif "playlist" in url:
        data = sp.playlist_tracks(url)
        for item in data["items"]:
            track = item["track"]
            tracks.append(f"{track['artists'][0]['name']} {track['name']}")
    return tracks
