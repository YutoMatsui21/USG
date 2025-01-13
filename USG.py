import openpyxl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Spotify APIのクライアントを作成
client_id = "91405ab57f864c65ad51dd759549a019"
client_secret = "b2c117ee89e14f7488f2d27ff6be7962"
client_credentials_manager = SpotifyClientCredentials(
    client_id=client_id, client_secret=client_secret
)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# 曲名とアルバム名を取得する
results = sp.search(q='artist:UNISON SQUARE GARDEN', type='track', limit=50)
tracks = results['tracks']['items']
track_info = []
for track in tracks:
    album_name = track['album']['name']
    track_name = track['name']
    track_id = track['id']
    track_info.append((album_name, track_name, track_id))

# Excelファイルを作成し、ヘッダー行を挿入
wb = openpyxl.Workbook()
ws = wb.active
ws.append(['アルバム名', '曲名', '長さ', 'BPM', '拍子'])

# 各曲の詳細情報を取得して、Excelに書き込む
for album_name, track_name, track_id in track_info:
    track_features = sp.audio_features(track_id)[0]
    duration_ms = track_features['duration_ms']
    duration = f"{int(duration_ms/60000)}分{int((duration_ms%60000)/1000)}秒"
    tempo = track_features['tempo']
    time_signature = track_features['time_signature']
    ws.append([album_name, track_name, duration, tempo, time_signature])

# Excelファイルを保存
wb.save('USG_tracks.xlsx')