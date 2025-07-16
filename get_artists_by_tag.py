# This script is designed to collect a list of music artists from the Last.fm API.
# It works by first finding artists associated with specific genre tags (e.g., "techno", "house")
# and then fetching the total number of listeners for each unique artist.
# The final output is a CSV file containing artist names, their listener counts, and their associated tags.
# This data can then be used to identify "underground" artists who have fewer listeners.

import requests
import csv
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
# Replace this with your own Last.fm API key if you have one.
API_KEY = os.getenv("API_KEY")

# These are the genres we want to search for. You can add or remove tags here.
TAGS = ["minimal", "house", "tech house", "deep house", "techno"]
# This sets how many artists the API should return in a single request (page).
LIMIT_PER_PAGE = 500
# This is the maximum number of pages we will request for each tag.
# For example, 20 pages * 500 artists/page = up to 10,000 artists per tag.
MAX_PAGES = 20
# The name of the file where we will save our results.
OUTPUT_FILE = "lastfm_artists_with_listeners.csv"

def get_top_artists_by_tag(tag, api_key, limit=500, max_pages=5):
    """
    Fetches a list of top artists for a specific tag from the Last.fm API.
    It can go through multiple pages to get a large number of artists.
    """
    artists = []
    # Loop through the pages of results from 1 up to our specified maximum.
    for page in range(1, max_pages + 1):
        print(f"Fetching tag '{tag}', page {page}")
        url = "https://ws.audioscrobbler.com/2.0/"
        params = {
            "method": "tag.gettopartists",
            "tag": tag,
            "api_key": api_key,
            "format": "json",
            "limit": limit,
            "page": page
        }
        # Make the request to the Last.fm API.
        response = requests.get(url, params=params)
        # If the API doesn't return a success code, we stop trying for this tag.
        if response.status_code != 200:
            print(f"Failed to fetch page {page} for tag {tag} with status {response.status_code}")
            break
        # Parse the JSON response from the API.
        data = response.json()
        # Extract the list of artists from the response data.
        page_artists = data.get("topartists", {}).get("artist", [])
        # If the API returns an empty list of artists, it means we've reached the end.
        if not page_artists:
            break
        # Add the artists from this page to our main list. We store them as a (name, tag) pair.
        artists.extend([(a["name"], tag) for a in page_artists])
        # We wait a little bit here to be polite to the Last.fm API and not send requests too fast.
        time.sleep(0.25)
    return artists

def get_artist_listeners(artist_name, api_key):
    """
    For a single artist, fetches their total listener count from the Last.fm API.
    This is what we use to measure how popular or "underground" an artist is.
    """
    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "artist.getinfo",
        "artist": artist_name,
        "api_key": api_key,
        "format": "json"
    }
    try:
        # Make the request to the API.
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"Failed to fetch info for {artist_name}: status {response.status_code}")
            return None # Return nothing if the request failed.
        # Parse the JSON and navigate through the data to find the listener count.
        data = response.json()
        listeners = data["artist"]["stats"]["listeners"]
        return int(listeners)
    except Exception as e:
        # If anything goes wrong (e.g., artist not found, network error), we print an error and return nothing.
        print(f"Error fetching listeners for {artist_name}: {e}")
        return None

def main():
    """
    This is the main function that runs the entire process.
    """
    print("Starting to fetch artists by tag...")
    # This list will hold all the (artist, tag) pairs we find.
    all_artist_tag_pairs = []
    # Loop through each of our defined tags and get the top artists for it.
    for tag in TAGS:
        artists = get_top_artists_by_tag(tag, API_KEY, LIMIT_PER_PAGE, MAX_PAGES)
        all_artist_tag_pairs.extend(artists)

    print(f"Fetched {len(all_artist_tag_pairs)} artist-tag pairs.")

    print("Deduplicating artists...")
    # This is a crucial step for efficiency. We want to avoid asking for the same artist's
    # listener count multiple times if they appear under different tags.
    # We use a dictionary where each key is an artist's name and the value is a set of all their tags.
    # This automatically handles uniqueness - an artist can only be a key once.
    artist_tags = {}
    for artist, tag in all_artist_tag_pairs:
        # .setdefault() is a handy way to add the artist if they're not in the dictionary yet.
        artist_tags.setdefault(artist, set()).add(tag)

    print(f"Unique artists found: {len(artist_tags)}")

    # --- THIS IS THE SLOWEST PART OF THE SCRIPT ---
    print("Fetching listener counts for unique artists...")
    # This dictionary will store the listener count for each unique artist.
    artist_listeners = {}
    # We loop through every unique artist we found.
    for idx, artist in enumerate(artist_tags.keys(), 1):
        # For each one, we call our function to get their listener count from the API.
        listeners = get_artist_listeners(artist, API_KEY)
        artist_listeners[artist] = listeners
        # Print a progress update every 50 artists so we know the script is still working.
        if idx % 50 == 0:
            print(f"Processed {idx}/{len(artist_tags)} artists")
        # We wait here again to be polite to the API.
        time.sleep(0.25)

    print(f"Writing output to {OUTPUT_FILE}...")
    # Now we open our output file in "write" mode.
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Write the header row for our CSV file.
        writer.writerow(["artist_name", "listeners", "tag"])
        # Loop through our dictionary of unique artists and their tags.
        for artist, tags in artist_tags.items():
            # Get the listener count we fetched earlier.
            listeners = artist_listeners.get(artist)
            # An artist might have multiple tags, so we write a separate row for each one.
            for tag in tags:
                writer.writerow([artist, listeners if listeners is not None else "", tag])

    print("Done!")

# This is standard Python practice. It means the `main()` function will only run
# when you execute the script directly (e.g., `python3 get_artists_by_tag.py`).
if __name__ == "__main__":
    main()
