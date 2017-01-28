from flask import Flask, redirect, render_template, request
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json

app = Flask(__name__)

# Flask Parameters
CLIENT_SIDE_URL = "http://192.168.1.25"
PORT = 5000
REDIRECT_URI = "{}:{}/playlists".format(CLIENT_SIDE_URL, PORT)
SCOPE = ("playlist-modify-public playlist-modify-private "
         "playlist-read-collaborative playlist-read-private")

#app.config.from_envar('PLAYLIST_ANALYSER', silent=True)

@app.route("/")
def index():
    """Redirect user to Spotify login/auth."""
    # TODO: Probably should add a Login page?
    sp_oauth = get_oauth()
    return redirect(sp_oauth.get_authorize_url())

@app.route("/playlists")
def get_playlist_info():

    spotify = get_spotify()
    if request.args.get("code"):
        get_spotify(request.args["code"])

    total_playlists = spotify.current_user_playlists()

    playlist_id = total_playlists["items"][6]["id"]

    print(total_playlists["items"][6]["name"])

    user_id = spotify.current_user()["id"]

    playlist = spotify.user_playlist(user_id, playlist_id)["tracks"]

    # print(json.dumps(playlist,indent=4))
    print(playlist["href"])

    while playlist:
        for tracks in playlist["items"]:
            print(tracks["track"]["album"]["name"])
        if playlist['next']:
            playlist = spotify.next(playlist)
        else:
            playlist = None
    return playlist_id


def get_oauth():
    """Return a Spotipy Oauth2 object."""
    prefs = get_prefs()
    return spotipy.oauth2.SpotifyOAuth(
        prefs["ClientID"], prefs["ClientSecret"], REDIRECT_URI, scope=SCOPE,
        cache_path=".tokens")

def get_prefs():
    """Get application prefs plist and set secret key.
    Args:
        path: String path to a plist file.
    """
    with open("config.json") as prefs_file:
        prefs = json.load(prefs_file)
    app.secret_key = prefs["SecretKey"]

    return prefs

def get_spotify(auth_token=None):
    """Return an authenticated Spotify object."""
    oauth = get_oauth()
    token_info = oauth.get_cached_token()
    if not token_info and auth_token:
        token_info = oauth.get_access_token(auth_token)
    return spotipy.Spotify(token_info["access_token"])


# @app.route('/')
# def home():
#     client_credentials_manager = SpotifyClientCredentials()
#     sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
#
#     playlists = sp.user_playlist('tumblerer','37i9dQZF1CyS7pa9xmes9h')
#     while playlists:
#         for i, playlist in enumerate(playlists['items']):
#             print("%4d %s %s" % (i + 1 + playlists['offset'], playlist['uri'],  playlist['name']))
#         if playlists['next']:
#             playlists = sp.next(playlists)
#         else:
#             playlists = None
#
#     return (al_list)
