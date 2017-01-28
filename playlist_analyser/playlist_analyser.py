from flask import Flask, redirect, render_template

app = Flask(__name__)

#app.config.from_envar('PLAYLIST_ANALYSER', silent=True)

@app.route('/')
def home():
    return ('Hello this is the analyser for Spotify')

