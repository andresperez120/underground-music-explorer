import requests
import pandas as pd
import time

# 🔐 Paste your Last.fm credentials here
API_KEY = 'cb5203f707d4c6316025145b3c031680'
SHARED_SECRET = 'your_lastfm_shared_secret_here'
BASE_URL = 'http://ws.audioscrobbler.com/2.0/'

def get_artist_top_tracks(artist_name, limit=50):
    """Get top tracks for an artist from Last.fm"""
    params = {
        'method': 'artist.gettoptracks',
        'artist': artist_name,
        'api_key': API_KEY,
        'format': 'json',
        'limit': limit
    }
    
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

def get_track_info(artist_name, track_name):
    """Get detailed track information"""
    params = {
        'method': 'track.getInfo',
        'api_key': API_KEY,
        'artist': artist_name,
        'track': track_name,
        'format': 'json'
    }
    
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_track_tags(artist_name, track_name):
    """Get tags (genres) for a track"""
    params = {
        'method': 'track.gettoptags',
        'api_key': API_KEY,
        'artist': artist_name,
        'track': track_name,
        'format': 'json'
    }
    
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Search for an underground artist's tracks
artist_name = "Prunk"
print(f"Getting tracks for {artist_name}...")

# Get top tracks
top_tracks_data = get_artist_top_tracks(artist_name, limit=20)

if not top_tracks_data:
    print("Could not retrieve track data")
    exit()

track_data = []

if 'toptracks' in top_tracks_data and 'track' in top_tracks_data['toptracks']:
    tracks = top_tracks_data['toptracks']['track']
    
    for i, track in enumerate(tracks):
        print(f"Processing track {i+1}/{len(tracks)}: {track['name']}")
        
        # Get detailed track info
        track_info = get_track_info(artist_name, track['name'])
        track_tags = get_track_tags(artist_name, track['name'])
        
        # Extract basic track data
        track_entry = {
            'track_name': track['name'],
            'artist': track['artist']['name'],
            'playcount': int(track['playcount']) if track.get('playcount') else 0,
            'listeners': int(track['listeners']) if track.get('listeners') else 0,
            'url': track.get('url', ''),
            'mbid': track.get('mbid', ''),
        }
        
        # Add detailed info if available
        if track_info and 'track' in track_info:
            track_detail = track_info['track']
            track_entry.update({
                'duration': int(track_detail.get('duration', 0)) / 1000 if track_detail.get('duration') else None,  # Convert to seconds
                'album': track_detail.get('album', {}).get('title', '') if track_detail.get('album') else '',
                'summary': track_detail.get('wiki', {}).get('summary', '') if track_detail.get('wiki') else ''
            })
        
        # Add tags if available
        if track_tags and 'toptags' in track_tags and 'tag' in track_tags['toptags']:
            tags = [tag['name'] for tag in track_tags['toptags']['tag'][:5]]  # Top 5 tags
            track_entry['top_tags'] = ', '.join(tags)
        else:
            track_entry['top_tags'] = ''
        
        track_data.append(track_entry)
        
        # Be nice to the API - add a small delay
        time.sleep(0.2)

# Convert to DataFrame
df = pd.DataFrame(track_data)

# Data processing
df = df.drop_duplicates(subset=['track_name'])
df = df.sort_values(by='playcount', ascending=False)

print("\nTrack data:")
print(df.head())
print(f"\nColumns: {list(df.columns)}")
print(f"\nDataset shape: {df.shape}")
print("\nBasic statistics:")
print(df[['playcount', 'listeners', 'duration']].describe())

# Save to CSV
df.to_csv('priku_tracks_lastfm.csv', index=False)
print(f"\nData saved to 'priku_tracks_lastfm.csv'")
