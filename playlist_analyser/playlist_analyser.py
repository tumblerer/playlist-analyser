from flask import Flask, redirect, render_template, request, session
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
import pygal
from urllib.request import urlopen
from collections import Counter, OrderedDict
from datetime import datetime
import sys
import time

app = Flask(__name__)

# Flask Parameters
CLIENT_SIDE_URL = "http://192.168.1.25"
PORT = 5000
if len(sys.argv) > 1:
    REDIRECT_URI = "{}:{}/".format(CLIENT_SIDE_URL, PORT)
else:
    REDIRECT_URI = "http://146.198.217.109/"
SCOPE = ("playlist-read-collaborative playlist-read-private")

# Control how many playlists can be analysed at a time
PLAYLIST_NUMBER = 2
#app.config.from_envar('PLAYLIST_ANALYSER', silent=True)

@app.route("/")
def index():
    """Redirect user to Spotify login/auth."""

    # Check response on login
    sp_oauth = get_oauth()
    if request.args.get("code"):
        code = request.args.get("code")
        token_info = sp_oauth.get_access_token(code)
        session['token'] = token_info

    if 'token' in session:
        logged_in = True

        # Check whether token needs a refresh
        token_info = session.get('token')
        if is_token_expired(token_info):
            session['token'] = sp_oauth.refresh_access_token(token_info["refresh_token"])
    else:
        logged_in = False

    return render_template('index.html', logged_in=logged_in,
                            playlist_number=PLAYLIST_NUMBER)


@app.route("/login")
def login():

    sp_oauth = get_oauth()
    return redirect(sp_oauth.get_authorize_url())


@app.route("/playlists", methods=['POST'])
def get_playlist_info():

    spotify = get_spotify()
    valid_playlsts = 0
    all_playlists_data = {}
    all_playlists_dates = {}

    for playlist_count in range(0,PLAYLIST_NUMBER):
        playlist_form = 'playlist_uri' + str(playlist_count)
        print(playlist_form)
        # If playlist form is empty, quit loop
        # TODO: validate text entry properly
        if request.form[playlist_form] == '':
            break
        else:
            valid_playlsts = valid_playlsts + 1

        print("check")
        playlist_uri = request.form[playlist_form]

        if playlist_uri[0:4] == 'http':
            # https://open.spotify.com/user/spotify/playlist/37i9dQZF1CyS7pa9xmes9h
            split_uri = playlist_uri.split('/')
        else:
            # spotify:user:spotify:playlist:37i9dQZF1CyS7pa9xmes9h
            split_uri = playlist_uri.split(":")

        username = split_uri[-3]
        playlist_id = split_uri[-1]

        user_id = username

        # Check length of playlist

        playlist_fetch = spotify.user_playlist(user_id, playlist_id,fields='tracks.total, name')
        playlist_length = playlist_fetch['tracks']['total']
        playlist_name = playlist_fetch['name']

        # dump_data(playlist)

        # Format (name, ID)
        tracks = []
        albums = []
        artists = []
        dates = []
        genre = []
        countries = []

        playlist_remaining = playlist_length
        offset = 0
        item_count = 0

        while playlist_remaining > 0:
            playlist = spotify.user_playlist_tracks(user_id, playlist_id,offset=offset)
            for items in playlist["items"]:
                # print(items["track"]["name"])
                track_info = [items["track"]["name"], items["track"]["id"]]
                tracks.append(track_info)
                album_info = [items["track"]["album"]["name"], items["track"]["album"]["id"]]
                albums.append(album_info)
                artist_info =  [items["track"]["artists"][0]["name"], items["track"]["artists"][0]["id"]]
                artists.append(artist_info)
                genre.append("genre_info")

            # Limit of 100 tracks in fetch
            playlist_remaining = playlist_remaining - 100
            offset = playlist_length - playlist_remaining

        dates = get_dates_from_album(albums, playlist_length)
        all_playlists_dates[playlist_name] = dates

        playlist_data = [playlist_id]

        for track, album, artist, date, genre in zip(tracks, albums, artists, dates, genre):
            meta_object = track_metadata(track, album, artist, date, genre)
            playlist_data.append(meta_object)

        all_playlists_data[playlist_id] = playlist_data

    # print(all_playlists_dates)
    dates_chart = generate_dates_chart(all_playlists_dates)


    return render_template('playlist.html', data=all_playlists_data, dates_chart=dates_chart)

def get_dates_from_album(album_info, total):

    spotify = get_spotify()

    dates = []
    ids = []

    offset = 0
    albums_remaining = total

    while albums_remaining > 0:
        # Build list of 20 ids
        # Limit of 20 songs in query
        if albums_remaining < 20:
            albums_remaining_20 = albums_remaining
        else:
            albums_remaining_20 = 20

        while albums_remaining_20 > 0:
            ids.append(album_info[offset][1])
            offset = offset + 1
            albums_remaining_20 = albums_remaining_20 - 1

        # dates = spotify.albums(ids)["release_date"][:4]
        albums = spotify.albums(ids)["albums"]
        albums_remaining = albums_remaining - 20
        # ID array needs to be reset every loop
        ids = []
        for entry in albums:
            date = entry["release_date"][:4]
            dates.append(int(date))

    return dates

def get_genre_from_artist(artists):


    return genre

def generate_dates_chart(total_dates):

    # Create list of dates
    playlist_names, dates = zip(*total_dates.items())

    min_date = min(dates[0])
    if min_date > 1950:
        min_date = 1950
    max_date = datetime.now().year

    # create a bar chart
    title = 'Songs Per Year'
    bar_chart = pygal.Bar(width=1200, height=600,
                          x_labels_major_every=3, show_minor_x_labels=False,
                          explicit_size=True, title=title, x_label_rotation=20)

    playlist_count = len(total_dates)

    for playlists in playlist_names:

        dates = total_dates[playlists]
        date_count = Counter(dates)

        for i in range(min_date,max_date):
            if not date_count[i]:
                date_count[i] = 0

        date_count_sorted = OrderedDict(sorted(date_count.items()))

        date, date_count = zip(*date_count_sorted.items())

        playlist_name = str(playlists)
        bar_chart.x_labels = date
        bar_chart.add(playlist_name, date_count)

    #bar_chart = pygal.StackedLine(width=1200, height=600,
    #                      explicit_size=True, title=title, fill=True)
    # bar_chart.render_to_file('bar_chart.svg')
    # bar_chart = bar_chart.render_data_uri()

    return bar_chart

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
        prefs["ClientID"], prefs["ClientSecret"], REDIRECT_URI, scope=SCOPE)

def get_prefs():
    """Get application prefs plist and set secret key.
    Args:
        path: String path to a plist file.
    """
    with open("config.json") as prefs_file:
        prefs = json.load(prefs_file)
    app.secret_key = prefs["CookieKey"]

    return prefs

def get_spotify(auth_token=None):
    """Return an authenticated Spotify object."""
    oauth = get_oauth()
    # token_info = oauth.get_cached_token()
    token_info = False
    if 'token' in session:
        token_info = session.get('token')
    if not token_info and auth_token:
        token_info = oauth.get_access_token(auth_token)

    return spotipy.Spotify(token_info['access_token'])

def is_token_expired(token_info):
    now = int(time.time())
    return token_info['expires_at'] - now < 180

app.secret_key = get_prefs()["CookieKey"]
