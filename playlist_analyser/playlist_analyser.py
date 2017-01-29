from flask import Flask, redirect, render_template, request
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json

app = Flask(__name__)

# Flask Parameters
CLIENT_SIDE_URL = "http://192.168.1.25"
PORT = 5000
REDIRECT_URI = "{}:{}/".format(CLIENT_SIDE_URL, PORT)
SCOPE = ("playlist-read-collaborative playlist-read-private")

#app.config.from_envar('PLAYLIST_ANALYSER', silent=True)

@app.route("/")
def index():
    """Redirect user to Spotify login/auth."""

    oauth = get_oauth()
    token_info = oauth.get_cached_token()
    if request.args.get("code"):
        get_spotify(request.args["code"])
    if not token_info:
        logged_in = False
    else:
        logged_in = True

    print('Logged IN ' + str(logged_in))
    return render_template('index.html', logged_in=logged_in)


@app.route("/login")
def login():

    sp_oauth = get_oauth()
    return redirect(sp_oauth.get_authorize_url())


@app.route("/playlists", methods=['POST'])
def get_playlist_info():

    spotify = get_spotify()
    if request.args.get("code"):
        get_spotify(request.args["code"])

    playlist_id = request.form["playlist_uri"][-22:]
    print(playlist_id)
    # print(total_playlists["items"][6]["name"])

    user_id = spotify.current_user()["id"]

    playlist = spotify.user_playlist(user_id, playlist_id)["tracks"]

    dump_data(playlist)

    # Format (name, ID)
    tracks = []
    albums = []
    artists = []
    dates = []
    genre = []
    countries = []

#    while playlist:
    for items in playlist["items"]:
        # print(items["track"]["name"])
        track_info = [items["track"]["name"], items["track"]["id"]]
        tracks.append(track_info)
        album_info = [items["track"]["album"]["name"], items["track"]["album"]["id"]]
        albums.append(album_info)
        artist_info =  [items["track"]["artists"][0]["name"], items["track"]["artists"][0]["id"]]
        artists.append(artist_info)
        genre.append("genre_info")

    dates = get_dates_from_album(albums)

    data = []
    for track, album, artist, date, genre in zip(tracks, albums, artists, dates, genre):
        meta_object = track_metadata(track, album, artist, date, genre)
        data.append(meta_object)

    test_a = ["a1","a2"]
    test_b = ["b1","b2"]
    test_data1 = track_metadata(test_a, "b", "c", "d", "e")
    test_data2 = track_metadata(test_b, "b", "c", "d", "e")

    test_data = [test_data1, test_data2]

    return render_template('playlist.html', data=data)

def get_dates_from_album(albums):

    spotify = get_spotify()

    dates = []
    for entry in albums:
        ids = entry[1]
        date = spotify.album(ids)["release_date"][:4]
        dates.append(date)

    return dates

def get_genre_from_artist(artists):


    return genre

def dump_data(json_data):

    f = open('example.json', 'w')
    f.write(json.dumps(json_data,indent=3))
    f.close()
    return

class track_metadata:
    """Object that contains all the meta data for a particular track"""
    def __init__(self, track, album, artist, date, genre):
        self.track = track
        self.artist = artist
        self.album = album
        self.date = date
        self.genre = genre


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
