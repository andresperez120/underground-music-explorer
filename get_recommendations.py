"""
This script is the core of the Underground Music Discovery Engine.

Its main purpose is to generate a personalized playlist of track recommendations
for a user, based on a single "seed artist" they provide.

The engine uses a sophisticated hybrid approach to ensure the playlist is both
relevant and exciting:

1.  Path A: The Relevance Engine
    - It finds artists who are musically similar to the user's seed artist.
    - It then grabs the top tracks from these similar artists. These are songs
      the user is very likely to enjoy.

2.  Path B: The Discovery Engine
    - It uses our pre-compiled artist database to find artists in the same
      genre as the seed artist, but who are "underground" (have a very low
      number of listeners).
    - It then grabs the top tracks from these hidden gems, introducing the
      user to new music.

Finally, the script combines the tracks from both paths into a single, ranked
playlist, ready for the user to explore.
"""
import pandas as pd
import requests
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("API_KEY")
ARTIST_DATA_CSV = "lastfm_artists_with_listeners.csv"

# load the data
def load_artist_data():
    """Loads the artist data from our CSV file."""
    try:
        df = pd.read_csv(ARTIST_DATA_CSV)
        # Drop rows with missing listeners for clean calculations
        df.dropna(subset=['listeners'], inplace=True)
        df['listeners'] = df['listeners'].astype(int)
        print("Artist data loaded successfully.")
        return df
    except FileNotFoundError:
        print(f"ERROR: The file {ARTIST_DATA_CSV} was not found.")
        print("Please run get_artists_by_tag.py first to generate the data.")
        return None

# api calls
def get_similar_artists(artist_name, api_key, limit=10):
    """
    Fetches a list of artists similar to a given artist from the Last.fm API.
    """
    print(f"   > Finding artists similar to {artist_name}...")
    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "artist.getsimilar",
        "artist": artist_name,
        "api_key": api_key,
        "format": "json",
        "limit": limit
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()
        
        # The data might not contain the 'similarartists' key if none are found
        similar_artists_data = data.get("similarartists", {}).get("artist", [])
        
        # Extract just the names of the artists
        artist_names = [artist['name'] for artist in similar_artists_data]
        
        if not artist_names:
            print(f"   > Found no similar artists for {artist_name}.")
        else:
            print(f"   > Found: {', '.join(artist_names)}")
            
        return artist_names
        
    except requests.exceptions.RequestException as e:
        print(f"   > ERROR: Network error while fetching similar artists for {artist_name}: {e}")
        return []
    except KeyError:
        # This can happen if the API response format is unexpected
        print(f"   > ERROR: Could not parse API response for {artist_name}.")
        return []

def get_top_tracks_for_artists(artist_names, api_key, limit_per_artist=5):
    """
    Fetches the top tracks for a list of artists.
    Returns a dictionary mapping each artist to a list of their top tracks.
    """
    artist_tracks_map = {}
    print(f"   > Fetching top {limit_per_artist} tracks for {len(artist_names)} artists...")
    
    for artist_name in artist_names:
        url = "https://ws.audioscrobbler.com/2.0/"
        params = {
            "method": "artist.gettoptracks",
            "artist": artist_name,
            "api_key": api_key,
            "format": "json",
            "limit": limit_per_artist
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            tracks_data = data.get("toptracks", {}).get("track", [])
            
            # Store the tracks under the artist's name
            artist_tracks_map[artist_name] = [f"{track['artist']['name']} - {track['name']}" for track in tracks_data]
            
            # Be polite to the API
            time.sleep(0.25)
            
        except requests.exceptions.RequestException as e:
            print(f"   > ERROR: Network error fetching tracks for {artist_name}: {e}")
            continue # Skip to the next artist
        except KeyError:
            print(f"   > ERROR: Could not parse tracks for {artist_name}.")
            continue
            
    print(f"   > Found tracks for {len(artist_tracks_map)} artists.")
    return artist_tracks_map

# discovery logic
def find_underground_artists(seed_artist, artist_df, percentile_threshold=0.75, max_artists=10):
    """
    Finds underground artists in the same genre as the seed artist.
    """
    print(f"   > Finding underground artists in the same genre as {seed_artist}...")
    
    # 1. Find the tags for the seed artist from our dataframe (case-insensitive search)
    seed_artist_tags = artist_df[artist_df['artist_name'].str.lower() == seed_artist.lower()]['tag'].unique()
    
    if len(seed_artist_tags) == 0:
        print(f"   > ERROR: Seed artist '{seed_artist}' not found in our data file.")
        return []
        
    # For simplicity, we'll use the first tag as the primary genre
    primary_genre = seed_artist_tags[0]
    print(f"   > Primary genre identified: {primary_genre}")
    
    # 2. Calculate the dynamic 'underground' threshold for that genre
    genre_df = artist_df[artist_df['tag'] == primary_genre]
    listener_threshold = genre_df['listeners'].quantile(percentile_threshold)
    print(f"   > Dynamic listener threshold for '{primary_genre}' (at {percentile_threshold:.0%}): {listener_threshold:,.0f} listeners")
    
    # 3. Filter for artists in that genre below the threshold
    underground_artists_df = genre_df[genre_df['listeners'] <= listener_threshold]
    
    # Exclude the seed artist themselves from the recommendations (case-insensitive)
    underground_artists_df = underground_artists_df[underground_artists_df['artist_name'].str.lower() != seed_artist.lower()]
    
    if underground_artists_df.empty:
        print("   > Found no other underground artists in this genre.")
        return []

    # 4. Return a sample of the unique artist names found
    underground_artist_names = underground_artists_df['artist_name'].unique()
    
    # We'll return a random sample to keep it fresh each time
    import random
    if len(underground_artist_names) <= max_artists:
        return list(underground_artist_names)
    else:
        return random.sample(list(underground_artist_names), max_artists)

def get_recommendations(seed_artist, artist_df, discovery_weight=0.5, playlist_size=20):
    """
    Main function to generate music recommendations.
    
    :param seed_artist: The artist to base recommendations on.
    :param artist_df: The DataFrame of artist data.
    :param discovery_weight: A float between 0.0 and 1.0. Determines the proportion of
                             underground 'discovery' tracks in the final playlist.
    :param playlist_size: The desired number of tracks in the final playlist.
    """
    print(f"\n--- Generating a playlist of {playlist_size} tracks for '{seed_artist}' ---")
    print(f"Discovery Weight: {discovery_weight:.0%}")

    # Dynamically determine how many artists to fetch based on playlist size.
    # We fetch more artists than needed to ensure we have enough tracks to choose from.
    num_artists_to_fetch = playlist_size

    # Path A: The Relevance Engine (similar artists)
    print("\nStep 1: Finding relevant tracks from similar artists...")
    # 1. Get similar artists to seed_artist from the API.
    similar_artists = get_similar_artists(seed_artist, API_KEY, limit=num_artists_to_fetch)
    # 2. Get top tracks for each of those similar artists from the API.
    relevant_artist_tracks = get_top_tracks_for_artists(similar_artists, API_KEY, limit_per_artist=5)

    # Path B: The Discovery Engine (underground artists)
    print("\nStep 2: Finding hidden gems from underground artists...")
    # 1. Find underground artists using our dynamic, genre-aware logic.
    underground_artists = find_underground_artists(seed_artist, artist_df, max_artists=num_artists_to_fetch)
    # 2. Get top tracks for those underground artists by reusing our existing function.
    discovery_artist_tracks = get_top_tracks_for_artists(underground_artists, API_KEY, limit_per_artist=5)

    # Step 3: The Mixer
    print("\nStep 3: Mixing and ranking the final playlist...")
    
    # Flatten the track lists from the dictionaries
    relevant_tracks = [track for tracks in relevant_artist_tracks.values() for track in tracks]
    discovery_tracks = [track for tracks in discovery_artist_tracks.values() for track in tracks]

    # 1. Determine the number of tracks to take from each path
    num_discovery_tracks = int(playlist_size * discovery_weight)
    num_relevant_tracks = playlist_size - num_discovery_tracks
    
    print(f"   > Taking {num_relevant_tracks} relevant tracks and {num_discovery_tracks} discovery tracks.")
    
    # 2. Combine the track lists, ensuring we don't have duplicates
    final_tracks = []
    
    # Add relevant tracks (ensuring no duplicates)
    for track in relevant_tracks:
        if len(final_tracks) < num_relevant_tracks and track not in final_tracks:
            final_tracks.append(track)
            
    # Add discovery tracks (ensuring no duplicates)
    for track in discovery_tracks:
        if len(final_tracks) < playlist_size and track not in final_tracks:
            final_tracks.append(track)

    # 3. Shuffle the final list to create a varied playlist
    import random
    random.shuffle(final_tracks)
    
    print(f"   > Generated a final playlist of {len(final_tracks)} unique tracks.")
    
    # Return a dictionary with both the playlist and the data for the graph
    return {
        "playlist": final_tracks,
        "similar_artists": relevant_artist_tracks,
        "underground_artists": discovery_artist_tracks
    }

if __name__ == '__main__':
    # Load the data once when the script starts
    artist_df = load_artist_data()

    if artist_df is not None:
        # TEST THE ENGINE
        test_artist = "Traumer" # Try 'Ricardo Villalobos' for minimal or 'Frankie Knuckles' for house
        
        # Test with a 70% focus on discovery
        results = get_recommendations(test_artist, artist_df, discovery_weight=0.7)
        recommended_tracks = results["playlist"]

        print("\n--- FINAL RECOMMENDATIONS ---")
        if recommended_tracks:
            for i, track in enumerate(recommended_tracks, 1):
                print(f"{i}. {track}")
        else:
            print("No recommendations generated yet.")
