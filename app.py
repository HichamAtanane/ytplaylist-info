from flask import Flask, render_template, request, url_for
import re
from urllib.parse import urlparse, parse_qs
from datetime import timedelta

from googleapiclient.discovery import build

api_key = 'AIzaSyDNy_C63SXBz9XBkDaBpDrIZM8KCJO8aK4'
youtube = build('youtube','v3', developerKey=api_key)
h_pattern = re.compile(r'(\d+)H')
m_pattern = re.compile(r'(\d+)M')
s_pattern = re.compile(r'(\d+)S')

def extract_playlist_id(playlist_url):
    # https://github.com/mps-youtube/pafy/blob/develop/pafy/playlist.py
    
    idregx = re.compile(r'((?:RD|PL|LL|UU|FL|OL)[-_0-9a-zA-Z]+)$')
    playlist_id = None
    if idregx.match(playlist_url):
        playlist_id = playlist_url  # ID of video

    if '://' not in playlist_url:
        playlist_url = '//' + playlist_url
    parsedurl = urlparse(playlist_url)
    if parsedurl.netloc in ('youtube.com', 'www.youtube.com'):
        query = parse_qs(parsedurl.query)
        if 'list' in query and idregx.match(query['list'][0]):
            playlist_id = query['list'][0]
    return playlist_id
def total_seconds(playlist_url):
    playlist_id = extract_playlist_id(playlist_url)
    nextPageToken = None
    total_seconds = 0
    while True:
        pl_request = youtube.playlistItems().list(
            part='contentDetails',
            playlistId = playlist_id,
            maxResults = 50,
            pageToken = nextPageToken
        )

        pl_response = dict(pl_request.execute())

        vid_ids = []
        for item in pl_response['items']:
            vid_ids.append(item['contentDetails']['videoId'])

        vid_request = youtube.videos().list(
            part = 'contentDetails',
            id=','.join(vid_ids)
        )

        vid_response = vid_request.execute()

        for item in vid_response['items']:
            duration = item['contentDetails']['duration']
            h = h_pattern.search(duration)
            m = m_pattern.search(duration)
            s = s_pattern.search(duration)
            
            h=int(h.group(1)) if h else 0 # in case h is none
            m=int(m.group(1)) if m else 0
            s=int(s.group(1)) if s else 0
            
            vid_seconds = timedelta(
                hours = h,
                minutes= m,
                seconds= s
            ).total_seconds()
            total_seconds += int(vid_seconds)   
        
        nextPageToken = pl_response.get('nextPageToken')
        if not nextPageToken:
            break 
        
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return [days, hours, minutes, seconds]

# ------------------------------------------------------------------------------------
  
app = Flask(__name__)

@app.route('/',methods = ['POST', 'GET'])
def calcul():
    if request.method == 'GET':
        return render_template("index.html")
    else:
        playlist_url = request.form['url']
        data = total_seconds(playlist_url)
        return render_template('index.html', result=data)

if __name__ == '__main__':
   app.run(debug = True)
   
   