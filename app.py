#imports for spotify access
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests

#import for Youtube access
import os
import google.oauth2.credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle
import yt_dlp as youtube_dl
from pytube import YouTube
import tkinter as tk
from tkinter import filedialog
from moviepy.editor import AudioFileClip
#ask the user for the download directory

#**************************************************************************************************************


# Access Spotify credentials from environment variables or directly set them
client_id = "YOUR-CLIENT-ID"
client_secret = 'YOUR-CLIENT-SECRET'
redirect_uri = 'YOUR-REDIRECT-URI'

#************************************************SOME ERROR HANDLING ******************************************

def get_integer_input(prompt):
    while True:
        try:
            user_input = int(input(prompt))
            return user_input
        except ValueError:
            print("Invalid input. Please enter a valid integer.")


#***************************************************************************************************************

def video_exists_in_playlist(youtube, playlist_id, video_id):
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlist_id,
        maxResults=50
    )
    response = request.execute()

    for item in response['items']:
        if item['snippet']['resourceId']['videoId'] == video_id:
            return True
    return False

#*****************************************************************************************************************

def add_song_to_youtube(youtube_video_id,youtube_client,selected_youtube_playlist):
    request = youtube_client.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": selected_youtube_playlist,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": youtube_video_id
                }
            }
        }
    )
    response = request.execute()
    print(f"SONG ADDED TO YOUTUBE PLAYLIST SUCCESSFULLY")

#********************************************************************************************************************


def get_songs_spotify_and_add_to_youtube(selected_spotify_playlist,access_token,youtube_client,selected_youtube_playlist):
    playlist_id = selected_spotify_playlist
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    playlist_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'

    response = requests.get(playlist_url, headers=headers)
    tracks = response.json()['items']

    for item in tracks:
        track = item['track']
        title = track['name']
        artist = track ['artists'][0]['name']
        print(track['name'], '-', track['artists'][0]['name'])

        #search for the song on youtube with song title and artist.
        search_query = f"{title} {artist}"
        request = youtube_client.search().list(
                        part='snippet',
                        q=search_query,
                        maxResults=2,
                        type='video'
                    )
        response = request.execute()
        youtube_video_id = response['items'][0]['id']['videoId']
        if not video_exists_in_playlist(youtube=youtube_client,playlist_id=selected_youtube_playlist,video_id=youtube_video_id):
            try:
                add_song_to_youtube(youtube_video_id,youtube_client,selected_youtube_playlist)
            except Exception as e:
                print(f"the song was not added because of {e}")
        else :
            print(" THE SONG ALREADY EXIST IN THE YOUTUBE PLAYLIST . ")

#*****************************************EXTRACT VIDEO ID FROM YOUTUBE.************************************************

def get_videos_id_from_playlist(youtube_client,playlist_id):
    videos_id = []
    request = youtube_client.playlistItems().list(
        part = "snippet,contentDetails",
        playlistId = playlist_id
    )
    videos_response = request.execute()

    for item in videos_response['items']:
        videos_id.append(item['contentDetails']['videoId'])
    return videos_id

#********************************************************************************************************************


#*********************************************************************************************************************

def add_song_by_title(song_title, playlist_id, access_token):
    sp = spotipy.Spotify(auth=access_token)
    results = sp.search(q=song_title, limit=1, type='track')
    tracks = results.get('tracks', {}).get('items', [])

    if not tracks:
        print(f"SONG '{song_title}' NOT FOUND.")
        return
    
    track_id = tracks[0]['id']

    playlist_tracks = sp.playlist_tracks(playlist_id)
    existing_tracks = [item['track']['id'] for item in playlist_tracks['items']]
    
    if track_id in existing_tracks:
        print(f"SONG '{song_title}' IS ALREADY IN THE SPOTIFY PLAYLIST.")
        return

    sp.playlist_add_items(playlist_id, [track_id])
    print(f"ADDED '{song_title}' TO THE SPOTIFY PLAYLIST .")
    
#********************************************************************************************************************
    

def get_title(video_id):
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"

    video = youtube_dl.YoutubeDL({'quiet':True}).extract_info(
        youtube_url,download = False
    )
    return (video['title'])

#********************************************************************************************************************

def get_songs_youtube_add_to_spotify(spotify_playlist_id,youtube_playlist_id,youtube_client,access_token):
    request = youtube_client.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=youtube_playlist_id,
        maxResults=50
    )
    response = request.execute()
    for item in response['items']:
        video_id = item['contentDetails']['videoId']
        title = get_title(video_id=video_id)
        add_song_by_title(song_title=title,playlist_id=spotify_playlist_id,access_token=access_token)
    
#*******************************************************************************************************************



#*****************************************DOWNLOAD PLAYLIST******************************************************

def download_playlist(youtube_client):

    request = youtube_client.playlists().list(part="snippet,contentDetails",
            maxResults=50,
            mine=True)
    response = request.execute()
    for idx,playlist in enumerate(response['items']):
        print(f"{idx+1}.{playlist['snippet']['title']}")
    print("----*-------------------------------*----")
    option_youtube= get_integer_input("WHICH PLAYLIST DO YOU WANT TO DOWNLOAD = ")

    for idx,item in (enumerate(response['items'])):
        if idx+1 == option_youtube:
            playlist_id = item['id']
            playlist_name = item['snippet']['title']
            print(f"YOU HAVE SELECTED {playlist_name} TO DOWNLOAD WITH SPOTube.")
        
    root = tk.Tk()
    root.withdraw() 
    download_dir = filedialog.askdirectory(title=" SELECT THE DIRECTORY TO DOWNLOAD THE PLAYLIST ")
    if download_dir :
        request =  youtube_client.playlistItems().list(
            part = "snippet,contentDetails",
            playlistId = playlist_id,
            maxResults=50,
            pageToken=None
                    )
        response = request.execute()
        for item in response['items']:
            video_id = item['contentDetails']['videoId']
            video_title = item ['snippet']['title']
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            yt = YouTube(video_url)
            audio_stream = yt.streams.filter(only_audio=True).first()
            if audio_stream:
                try:
                    temp_audio_file = audio_stream.download()
                    audio_clip = AudioFileClip(temp_audio_file)
                    mp3_filename = f'{video_title}.mp3'
                    mp3_path = f'{download_dir}/{mp3_filename}'
                    audio_clip.write_audiofile(mp3_path)
                    audio_clip.close()

                    print(f"AUDIO '{mp3_filename}' DOWNLOADED SUCCESSFULLY TO {download_dir}")
                except Exception as e:
                    print (f"THE AUDIO COULD NOT BE DOWNLOADED.ERROR = {e}")
            else:
                (f"NO AUDIO STREAM IS AVAILABLE FOR VIDEO ID = {video_id}")

    else :
        print("THE DOWNLOAD DIRECTORY WAS NOT SELECTED PROGRAM EXITING.")
        pass
        
#******************************************************************************************************************


def main(): 
    
    #************************************************SPOTIFY OAuth*************************************************
    
    scope = "playlist-read-private playlist-modify-private"
    sp_oauth = SpotifyOAuth(scope=scope,
                                                client_id=client_id,
                                                client_secret=client_secret,
                                                redirect_uri=redirect_uri,
                                                cache_path=None)
    access_token = sp_oauth.get_access_token(as_dict=False)
    # Initialize the Spotify client with the OAuth manager
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope,
                                                client_id=client_id,
                                                client_secret=client_secret,
                                                redirect_uri=redirect_uri,
                                                cache_path=None))
    results = sp.current_user_playlists(limit=50)
    for idx, playlist in enumerate(results['items']):
        print(f"{idx + 1}. {playlist['name']}")
    print("----*-------------------------------*----")
    option=get_integer_input("WHICH SPOTIFY PLAYLIST DO YOU WANT TO SYNC WITH SPOTube= ")
    

    for idx,playlist in enumerate(results['items']):
        if (idx+1)==option:
            selected_spotify_playlist_id = playlist['id']
            print (f"YOU HAVE SELECTED {playlist['name']} TO SYNC WITH SPOTube.")
    
    #************************************************************************************************************

    #***********************************************YOUTUBE OAuth************************************************

    SCOPES = ['https://www.googleapis.com/auth/youtube']
    CREDENTIALS_FILE = 'token.pickle'
    # Load or create new credentials
    creds = None
    if os.path.exists(CREDENTIALS_FILE):
        print('Loading Credentials From File...')
        with open(CREDENTIALS_FILE, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print('Refreshing Access Token...')
            creds.refresh(Request())
        else:
            print('Fetching New Tokens...')
            flow = InstalledAppFlow.from_client_secrets_file(
                r"PATH-TO-YOUR-GOOGLE-CLIENT-ID-AND-SECRET-JSON-FILE",
                SCOPES
            )
            creds = flow.run_local_server(
                port=5045,#CONFIGURE THE PORT ACCORDING YOUR GOOGLE REDIRECT URI.
                prompt='consent',
                authorization_prompt_message='YOUR ACCOUNT HAVE BEEN AUTHORISED SUCCESSFULLY'
            )
            with open(CREDENTIALS_FILE, 'wb') as f:
                print('Saving Credentials for Future Use...')
                pickle.dump(creds, f)
    youtube = build("youtube", "v3", credentials=creds)
    request = youtube.playlists().list(part="snippet,contentDetails",
            maxResults=50,
            mine=True)
    response = request.execute()
    for idx,playlist in enumerate(response['items']):
        print(f"{idx+1}.{playlist['snippet']['title']}")
    print("----*-------------------------------*----")
    option_youtube= get_integer_input("WHICH YOUTUBE PLAYLIST DO YOU WANT TO SYNC WITH SPOTube = ")

    for idx,item in (enumerate(response['items'])):
        if idx+1 == option_youtube:
            selected_youtube_playlist_id = item['id']
            selected_youtube_playlist_name = item['snippet']['title']
            print(f"YOU HAVE SELECTED {selected_youtube_playlist_name} TO SYNC WITH SPOTube.")
        

    #*************************************************************************************************************
    

    #*****************************************ADDING THE SONGS IN YOUTUBE PLAYLIST FROM SPOTIFY*******************
    
    get_songs_spotify_and_add_to_youtube(selected_spotify_playlist=selected_spotify_playlist_id,
                                         access_token=access_token,
                                         youtube_client=youtube,
                                         selected_youtube_playlist=selected_youtube_playlist_id)


    #****************************************ADDING THE SONGS IN SPOTIFY PLAYLIST FROM YOUTUBE**********************

    playlist_videos_id_list = get_videos_id_from_playlist(youtube_client=youtube,playlist_id=selected_youtube_playlist_id)

    for video_id in playlist_videos_id_list:
        title = get_title(video_id)
        add_song_by_title(song_title=title,playlist_id=selected_spotify_playlist_id,access_token=access_token)

    #*****************************************************************************************************************

    print("BOTH OF YOUR PLAYLISTS HAVE BEEN SYNCED 🎶")


    option = input ("DO YOU WANT TO DOWNLOAD PLAYLIST AS WELL.(Y/N)")
    if option == "Y":
        download_playlist(youtube_client=youtube)
    elif option =="N":
        pass
    else:
        print("INVALID CHOICE , PROGRAM EXITING")
    print(" THANKS FOR USING SPOTube. ENJOY YOUR MUSIC 😊")




if __name__=="__main__":
    main()
