import streamlit as st
from get_recommendations import load_artist_data, get_recommendations
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import numpy as np


# Page configuration
st.set_page_config(
    page_title="Underground House Music Discovery Engine",
    page_icon="🎵",
    layout="wide"
)


# Charting functions
def create_popularity_chart(recommendations, artist_df):
    """
    Creates a bar chart showing the listener counts for the recommended tracks.
    """
    # Set a dark theme for the plot to match the app
    plt.style.use("dark_background")

    # Extract artist names from the 'Artist - Track' strings
    recommended_artists = [rec.split(' - ')[0] for rec in recommendations]
    
    # Create a DataFrame for the recommended artists
    rec_df = pd.DataFrame({'artist_name': recommended_artists})
    
    # Merge with the main artist_df to get listener counts
    chart_df = pd.merge(rec_df, artist_df, on='artist_name', how='left').drop_duplicates(subset=['artist_name'])
    
    # Sort by listeners for a cleaner chart
    chart_df = chart_df.sort_values(by='listeners', ascending=True)

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Set background color to match Streamlit's dark theme
    fig.patch.set_facecolor('#0E1117')
    ax.set_facecolor('#0E1117')

    barplot = sns.barplot(data=chart_df, x='listeners', y='artist_name', ax=ax, color='#c0392b') # A nice red color
    
    # Add the listener count labels to the end of each bar
    ax.bar_label(
        barplot.containers[0], # type: ignore
        fmt='{:,.0f}',  # Format as an integer with commas
        padding=5,
        fontsize=10,
        color='white'
    )

    # Customize titles and labels for the dark theme
    ax.set_title('Popularity Spectrum of Your Recommended Artists', color='white')
    ax.set_xlabel('All-Time Listeners on Last.fm', color='white')
    ax.set_ylabel('')
    
    # Customize the plot's appearance for a modern look
    ax.tick_params(colors='white', which='both')
    for spine in ax.spines.values():
        spine.set_edgecolor('#555555') # Lighter gray for spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    
    return fig

def create_recommendation_galaxy(recommendations, artist_df):
    """
    Creates an interactive scatter plot of recommended songs, clustered by genre.
    Size represents artist popularity, color represents genre.
    """
    if not recommendations:
        return None

    # 1. Create a detailed DataFrame for the plot
    plot_data = []
    for rec in recommendations:
        artist_name, track_name = rec.split(' - ', 1)
        artist_info = artist_df[artist_df['artist_name'] == artist_name]
        if not artist_info.empty:
            plot_data.append({
                'artist_track': rec,
                'artist_name': artist_name,
                'Artist Listeners': artist_info.iloc[0]['listeners'],
                'genre': artist_info.iloc[0]['tag']
            })
    
    if not plot_data:
        st.info("Could not gather enough data to create the recommendation galaxy.")
        return None

    plot_df = pd.DataFrame(plot_data)

    # 2. Define cluster centers for top genres to avoid random scatter
    genre_counts = plot_df['genre'].value_counts()
    top_genres = list(genre_counts.head(5).index) # Convert to list
    centers = {} # Initialize centers dictionary
    
    # Simple spatial arrangement for clusters, only if we have enough genres
    if len(top_genres) >= 5:
        centers = {
            top_genres[0]: (0.25, 0.75),
            top_genres[1]: (0.75, 0.75),
            top_genres[2]: (0.5, 0.25),
            top_genres[3]: (0.1, 0.1),
            top_genres[4]: (0.9, 0.1)
        }
    else:
        # Fallback for fewer than 5 genres
        for genre in top_genres:
            centers[genre] = (np.random.rand(), np.random.rand())


    # 3. Assign coordinates to each song
    plot_df['x'] = 0.0
    plot_df['y'] = 0.0
    for i, row in plot_df.iterrows():
        genre = str(row['genre']) # Explicitly cast to string
        center_x, center_y = centers.get(genre, (0.5, 0.5)) # Default to center
        # Add jitter
        plot_df.loc[i, 'x'] = center_x + (np.random.rand() - 0.5) * 0.2
        plot_df.loc[i, 'y'] = center_y + (np.random.rand() - 0.5) * 0.2

    # 4. Create the plot
    fig = px.scatter(
        plot_df,
        x='x',
        y='y',
        size='Artist Listeners',
        color='genre',
        hover_name='artist_track',
        hover_data={'x': False, 'y': False, 'genre': False, 'Artist Listeners': ':,d'}, # Clean hover data
        size_max=50,
        template='plotly_dark'
    )

    fig.update_layout(
        title_text="Your Recommendation Galaxy",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title='', fixedrange=True),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title='', fixedrange=True),
        legend_title_text='Genres',
        annotations=[dict(
            text="<b>Circle Size</b> = Artist's All-Time Listeners",
            align='left',
            showarrow=False,
            xref='paper',
            yref='paper',
            x=0.0,
            y=-0.15,
            font=dict(size=11, color="grey")
        )]
    )

    return fig


# Data loading
# Use Streamlit's cache to load the data only once
@st.cache_data
def cached_load_artist_data():
    return load_artist_data()

artist_df = cached_load_artist_data()


# App layout
st.title("🎵 Underground House Music Discovery Engine")
st.write("Welcome! Enter an artist you like, and we'll find some hidden gems for you.")
st.write("With ❤️ from Andres")

# Use columns for a cleaner layout
col1, col2 = st.columns([2, 1])

with col1:
    seed_artist = st.text_input(
        label="Enter an artist name:",
        placeholder="e.g., Cristi Cons, Ricardo Villalobos"
    )

with col2:
    discovery_weight = st.slider(
        label="How adventurous do you want to be?",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.1,
        help="0.0 = More mainstream artists. 1.0 = Deeper underground cuts."
    )
    
    playlist_size = st.slider(
        label="Number of songs in my playlist:",
        min_value=5,
        max_value=30,
        value=20, # Default value
        step=1
    )

if st.button("✨ Find My Playlist ✨"):
    if not seed_artist:
        st.warning("Please enter an artist name.")
    elif artist_df is None:
        st.error("Artist data could not be loaded. Please check the logs.")
    else:
        with st.spinner("Calling the recommendation engine... this might take a moment..."):
            results = get_recommendations(
                seed_artist,
                artist_df,
                discovery_weight=discovery_weight,
                playlist_size=playlist_size
            )

        st.success("Playlist generated!")
        
        # Display the results
        recommendations = results["playlist"]
        num_recs = len(recommendations)
        if num_recs > 0:
            st.subheader("Your Custom Playlist:")
            # Use columns for the playlist to save vertical space
            num_columns = 2
            cols = st.columns(num_columns)
            for i, rec in enumerate(recommendations):
                cols[i % num_columns].write(f"{i+1}. {rec}")
            
            # Add a small note if the playlist is shorter than requested
            if num_recs < playlist_size:
                st.info(f"💡 We found {num_recs} great tracks! The playlist can be shorter than requested to ensure quality and avoid duplicates. Try adjusting the 'adventurous' slider for different results!")

            # Add a divider
            st.divider()

            # Create two columns for playlist and chart
            col1_chart, col2_galaxy = st.columns(2)

            with col1_chart:
                st.subheader("Popularity Spectrum:")
                fig = create_popularity_chart(recommendations, artist_df)
                st.pyplot(fig)
            
            with col2_galaxy:
                st.subheader("Recommendation Galaxy")
                galaxy_fig = create_recommendation_galaxy(recommendations, artist_df)
                if galaxy_fig:
                    st.plotly_chart(galaxy_fig, use_container_width=True)
                else:
                    st.info("Not enough genre data to create a galaxy map for these artists.")

        else:
            st.info("Could not generate recommendations. Try a different artist.") 