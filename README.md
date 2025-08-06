# 🚀 [Try the Underground House Music Discovery Engine!](https://underground-music-explorer.streamlit.app/)

# Underground Music Discovery Engine

## 🎯 Project Goal
To create an intelligent music discovery platform that helps users explore **underground electronic music** through multiple approaches:

1.  **Smart Recommendations**: A hybrid engine that balances familiar tracks (from similar artists) with hidden gems from underground artists in the same genres
2.  **Data-Driven Discovery**: Dynamic, genre-specific thresholds that intelligently define "underground" based on each genre's unique popularity distribution
3.  **Machine Learning Insights**: K-means clustering to reveal patterns in artist popularity and genre relationships, helping users understand the electronic music landscape

This multi-faceted approach delivers personalized recommendations while providing educational insights into how electronic music artists cluster and what makes them "underground."

---

## 🌐 Live Demo
- **Play with the app here:** [underground-music-explorer.streamlit.app](https://underground-music-explorer.streamlit.app/)

---

## ⚙️ Tech Stack & References
- **Python** (core logic)
- **Streamlit** (web app framework)
- **Pandas** (data manipulation and analysis)
- **Requests** (Last.fm API calls)
- **Scikit-learn** (K-means clustering and data preprocessing)
- **Matplotlib, Seaborn, Plotly** (static and interactive visualizations)
- **Last.fm API** ([docs](https://www.last.fm/api))

---

## 📊 Key Findings from EDA

Exploratory Data Analysis (EDA) was performed to understand the landscape of electronic music artists and listeners. Here are some highlights:

- **Artist Popularity is Extremely Skewed:**  
  The vast majority of artists have very few listeners, while a small number of artists are extremely popular.

  ![Overall View of Artist Popularity](images/overall_view_of_artist_popularirty.png)  
  *Left: Histogram of all artists by listener count (highly skewed). Right: Boxplot showing the same distribution.*

- **Zooming in on the Underground:**  
  Even when focusing on artists with fewer than 50,000 or 10,000 listeners, the distribution remains heavily skewed—most artists are truly underground.

  ![The Underground Artists](images/the_underground_artists.png)  
  *Left: Histogram for artists with <50k listeners. Right: Histogram for artists with <10k listeners.*

- **Listener Count by Genre Tag:**  
  Some genres (like techno and house) have a wider range of artist popularity, but the skewness persists across all genres.

  ![Listener Count Distribution by Genre (All)](images/listener_count_distribution_by_genre_tag_overall.png)  
  *Boxplot: Listener count distribution for each genre tag (all artists).*

  ![Listener Count Distribution by Genre (<50k)](images/listener_count_distribution_by_genre_tag_50000.png)  
  *Boxplot: Listener count distribution for each genre tag (artists with <50k listeners).*

  ![Listener Count Distribution by Genre (<10k)](images/listener_count_distribution_by_genre_tag_10000.png)  
  *Boxplot: Listener count distribution for each genre tag (artists with <10k listeners).*

**Key Insights:**
- The definition of “underground” is robust: even at low listener thresholds, most artists remain obscure.
- Genre does not eliminate the skew—underground status is a consistent phenomenon across electronic music.

**Additional EDA Findings:**
- **Popularity varies significantly by genre:**
    - House is mainstream: House artists have dramatically higher mean and max listener counts than any other genre, reflecting its broad appeal and superstar presence. The 'house' tag is also very broad and ambiguous.
    - Minimal is the most "underground": The minimal tag has the lowest median listener count—50% of all minimal artists have fewer than 195 all-time listeners, making it a highly niche genre.
    - Techno & House are neighbors: Techno, deep house, and tech house occupy a middle ground, with techno being slightly more popular on average than deep house or tech house.
- **Every genre is skewed:**
    - The boxplots and the large differences between mean and median listener counts for every tag confirm a power-law distribution: every genre has a handful of superstars and a massive long tail of unknown artists.

---

## 📦 Data Collection & Smart Thresholds

### Data Collection from Last.fm
- **Artist Discovery:** Used Last.fm's `tag.getTopArtists` endpoint to fetch thousands of artists for each genre tag (e.g., 'techno', 'house').
- **Popularity Metric:** Queried each artist's total listener count using the `artist.getInfo` endpoint.
- **Genre Tagging:** Collected the top genre tags for each artist.
- **Data Storage:** All artist/tag/listener data is stored in `lastfm_artists_with_listeners.csv`.

### Dynamic Underground Definition
Rather than using a fixed threshold, the system now employs **genre-specific, dynamic thresholds**:

- **25th-75th Percentile Band**: "Underground" artists fall between the 25th and 75th percentiles of listener counts within their specific genre
- **Genre-Aware Intelligence**: What's "underground" in house music (broader appeal) differs significantly from minimal techno (niche appeal)
- **Smart Filtering**: Ensures every genre has a viable pool of discoverable underground artists
- **No Impossible Constraints**: Eliminates scenarios where the minimum threshold exceeds the genre's 75th percentile

**Example**: In house music, underground artists might have 2,000-12,000 listeners, while in minimal, they might have 200-800 listeners.

---

## 🛠️ How the Data & Recommendations Work

### How do we build the artist database? (`get_artists_by_tag.py`)
This script is responsible for building the core artist database that powers the app:
1. **Finds artists by genre:** For each genre (like 'techno', 'house', etc.), it uses the Last.fm API to get a big list of artists.
2. **Removes duplicates:** Many artists appear under multiple genres. The script makes sure each artist is only counted once, but keeps track of all their genres.
3. **Gets popularity:** For every unique artist, it looks up their total number of listeners on Last.fm. This tells us how "underground" they are.
4. **Saves to CSV:** All this info—artist name, listener count, and genre(s)—is saved in a CSV file. This file is the foundation for all recommendations and analysis.

### How do we generate recommendations? (`get_recommendations.py`)
This script is the heart of the recommendation engine:
1. **Takes your favorite artist:** You enter an artist you like (the "seed").
2. **Finds similar artists:** Uses the Last.fm API to find artists similar to your seed artist, and gets their top tracks (familiar discoveries).
3. **Identifies genres dynamically:** Determines the seed artist's genre(s) from the database, including both solo entries and collaborations.
4. **Calculates smart thresholds:** For each genre, computes the 25th-75th percentile listener range to define "underground but discoverable."
5. **Finds underground artists:** Searches the database for artists within the underground range for those genres.
6. **Mixes intelligently:** Combines tracks from both streams using the "adventurous" slider to control the familiar/discovery balance.

### Machine Learning Artist Clustering
The app features an **"Explore Artist Clusters"** tab that uses unsupervised machine learning to reveal patterns in the electronic music landscape:

**Features Used for Clustering:**
- **Artist Popularity (Log-Transformed)**: Raw listener counts are log-transformed to handle the extreme skewness in music popularity data
- **Genre Mainstream-ness**: A calculated metric representing how "mainstream" vs "niche" each genre is based on average listener counts

**Why Log Transformation?**
- **Extreme skewness**: Most artists have <10k listeners while top artists have millions
- **Better clustering**: Prevents mega-popular artists from dominating all cluster assignments
- **Meaningful patterns**: Captures that the difference between 1k→10k listeners is as significant as 100k→1M listeners
- **Algorithm efficiency**: Creates balanced clusters based on popularity tiers rather than raw numbers

**Interactive Features:**
- **Adjustable cluster count**: Users can select 3-7 clusters to see different levels of granularity
- **Dynamic cluster descriptions**: Automatically generates meaningful names like "Mainstream Giants," "Underground Favorites," etc.
- **Cluster insights**: Shows average popularity, top genres, and example artists for each cluster
- **Interactive visualization**: Plotly-powered scatter plot with hover details and genre color-coding

**In summary:**
- `get_artists_by_tag.py` builds the comprehensive artist database
- `get_recommendations.py` uses dynamic thresholds and smart mixing for personalized playlists
- **Machine learning clustering** reveals the hidden structure of electronic music popularity and genre relationships

---

## 📑 Data Dictionary: `lastfm_artists_with_listeners.csv`
| Column Name   | Description                                                      |
|--------------|------------------------------------------------------------------|
| artist_name  | Name of the artist                                               |
| tag          | Primary genre tag (e.g., 'techno', 'house')                      |
| listeners    | Total number of unique Last.fm listeners for the artist          |


---

## 🚦 Project Phases (Actual Workflow)
1. **Data Collection**
    - Gathered artist/tag/listener data from Last.fm using `get_artists_by_tag.py`
    - Built comprehensive database of ~50k electronic music artists
  
2. **Exploratory Data Analysis (EDA)**
    - Analyzed the extreme skewness in music popularity across genres
    - Discovered genre-specific popularity patterns that informed dynamic threshold design
    
3. **Recommendation Engine Development**
    - Developed hybrid logic combining "relevance" (similar artists) and "discovery" (underground artists)
    - Implemented dynamic, genre-aware thresholds to replace fixed "underground" definitions
    - Enhanced collaboration matching for artists primarily known through features/remixes
    
4. **Machine Learning Integration**
    - Added K-means clustering with log-transformed features to reveal artist groupings
    - Built interactive cluster visualization and analysis tools
    - Implemented educational explanations of data science concepts
    
5. **Web App Development**
    - Built intuitive Streamlit interface with dual-tab navigation
    - Created comprehensive visualizations (bar charts, galaxy plots, cluster maps)
    - Added user-friendly explanations and transparent algorithm descriptions
    
6. **Deployment & Polish**
    - Deployed to Streamlit Community Cloud with proper secrets management
    - Enhanced user experience with helpful notes and data transparency features

---

## 🤝 Collaboration & Future Work
- **Explore song-level features:** I would love to learn more about the BPM (tempo) and other musical features of individual songs—especially those not available from public APIs. If you have ideas, data sources, or want to collaborate on extracting or inferring these features, please reach out!
- Add user authentication for personalized scrobble-based recommendations.




