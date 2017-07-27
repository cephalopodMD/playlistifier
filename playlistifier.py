import sys
import datetime, time
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
from flask import Flask, make_response
app = Flask(__name__)

@app.route('/')
def hello():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- The above 3 meta tags *must* come first in the head; any other head content must come *after* these tags -->
    <title>WXTJ's Super Electric Playlistifier</title>

    <link
      rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css"
      integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u"
      crossorigin="anonymous">
    <style>
    body {
      padding-top: 40px;
      padding-bottom: 40px;
      background-color: #eee;
    }

    .form-signin {
      max-width: 480px;
      padding: 15px;
      margin: 0 auto;
    }
    .form-signin .form-signin-heading,
    .form-signin .checkbox {
      margin-bottom: 10px;
      text-align: center;
    }
    .form-signin .form-control {
      position: relative;
      height: auto;
      -webkit-box-sizing: border-box;
         -moz-box-sizing: border-box;
              box-sizing: border-box;
      padding: 10px;
      font-size: 16px;
    }
    .form-signin .form-control:focus {
      z-index: 2;
    }
    .form-signin input {
      margin-bottom: 10px;
      border-top-left-radius: 0;
      border-top-right-radius: 0;
      text-align: center;
    }
    </style>

    <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
    <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/html5shiv/3.7.3/html5shiv.min.js"></script>
      <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->
  </head>
  
  <body>
    <div class="container">
      <form class="form-signin">
        <h2 class="form-signin-heading">The Super Electric Playlistifier</h2>
        <br/>
        <input id="inputURI" type='text' class="form-control" placeholder="spotify:user:1234567890:playlist:0Ab2C3d4F5g6H7i8J" required autofocus>
        <button class="btn btn-lg btn-primary btn-block" type="submit" id="submit">Submit Playlist URI</button>
        <br/>
        <p><small>Right click your playlist, click share, copy the URI, and paste it above for a handy csv!</small></p>
      </form>
    </div> <!-- /container -->

    <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js"></script>
    <script>
    $(document).ready(function() {
        $('#submit').click( function() {
            // wonky when relative path includes dev for aws lambda!!!
            window.open('/' + $('#inputURI').val());
        });
    });
    </script>
  </body>
</html>
'''

@app.route("/<uri>")
def csv(uri):
    target_playlist_user_id = uri.split(':')[2]
    target_playlist_id = uri.split(':')[4]

    from credentials import client_id, client_secret

    client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    def add_tracks(tracks):
        csv_chunk = ''
        for t in tracks['items']:
            track = t['track']
            t_time = str(datetime.timedelta(milliseconds=(track['duration_ms'] - track['duration_ms']%1000)))
            while t_time[0] in ':0':
                t_time = t_time[1:]
            artists = ','.join([artist['name'] for artist in track['artists']])
            album = sp.album(track['album']['id'])
            copyrights = ' // '.join([cr['text'] for cr in album['copyrights']])

            track_string = (
                '"' + track['name'] + '","' + \
                t_time + '","' + \
                artists + '","' + \
                track['album']['name'] + '","' + \
                album['release_date'][0:4] + '","' +
                copyrights + '","","",""\r').encode("ascii", errors='replace').decode('utf-8')

            csv_chunk += track_string
        return csv_chunk

    results = sp.user_playlist(target_playlist_user_id, target_playlist_id, fields="tracks,next,name")

    if 'tracks' not in results:
        return 'you must have a valid playlist uri!'
    tracks = results['tracks']
    csv = add_tracks(tracks)

    while tracks['next']:
        tracks = sp.next(tracks)
        csv += add_tracks(tracks)

    response = make_response(csv)
    response.headers["Content-Disposition"] = "attachment; filename=%s.csv"%results['name']
    return response
