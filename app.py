import streamlit as st
from get_recommendations import load_artist_data, get_recommendations
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


# Page configuration
st.set_page_config(
    page_title="Underground House Music Discovery Engine",
    page_icon="🎵",
    layout="wide"
)

# Add custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b6b;
    }
</style>
""", unsafe_allow_html=True)


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
    
    # Create a copy of artist_df with normalized names for better matching
    artist_df_normalized = artist_df.copy()
    artist_df_normalized['artist_name_norm'] = artist_df_normalized['artist_name'].str.lower().str.strip()
    
    # Normalize recommended artist names for matching
    rec_df['artist_name_norm'] = rec_df['artist_name'].str.lower().str.strip()
    
    # Merge with the main artist_df to get listener counts using normalized names
    chart_df = pd.merge(rec_df, artist_df_normalized, on='artist_name_norm', how='left')
    
    # Use the original artist names from recommendations for display
    chart_df = chart_df.drop_duplicates(subset=['artist_name_x'])
    chart_df = chart_df.rename(columns={'artist_name_x': 'artist_name'})
    
    # Filter out rows where no match was found (listeners is NaN)
    chart_df = chart_df.dropna(subset=['listeners'])
    
    # Check if we have any data to plot
    if chart_df.empty:
        # Create a simple message plot if no data matches
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#0E1117')
        ax.set_facecolor('#0E1117')
        ax.text(0.5, 0.5, 'No artist data found for visualization\n(Artist names may not match database)', 
                ha='center', va='center', transform=ax.transAxes, 
                color='white', fontsize=12)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        return fig
    
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
        # Use case-insensitive matching for better results
        artist_info = artist_df[artist_df['artist_name'].str.lower().str.strip() == artist_name.lower().strip()]
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


def prepare_clustering_data(artist_df):
    """
    Prepare artist data for clustering by creating features and handling missing values.
    """
    # Create a copy to avoid modifying the original
    df = artist_df.copy()
    
    # Handle missing values
    df = df.dropna(subset=['listeners', 'tag'])
    
    # Log transform listener counts to handle skewness
    df['log_listeners'] = np.log1p(df['listeners'])
    
    # Create genre diversity feature (how many different tags an artist has)
    # For now, we'll use a simple approach since each row has one tag
    df['genre_popularity'] = df.groupby('tag')['listeners'].transform('mean')
    df['log_genre_popularity'] = np.log1p(df['genre_popularity'])
    
    # Create features for clustering
    features = ['log_listeners', 'log_genre_popularity']
    
    return df, features


def perform_clustering(df, features, n_clusters=5):
    """
    Perform K-means clustering on artist data.
    """
    # Prepare feature matrix
    X = df[features].values
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Perform clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)
    
    # Add cluster labels to dataframe
    df_clustered = df.copy()
    df_clustered['cluster'] = cluster_labels
    
    return df_clustered, kmeans, scaler


def create_cluster_visualization(df_clustered):
    """
    Create an interactive cluster visualization.
    """
    # Sort clusters by average listener count for consistent naming
    cluster_means = df_clustered.groupby('cluster')['log_listeners'].mean().sort_values(ascending=False)
    cluster_mapping = {}
    for i, cluster_id in enumerate(cluster_means.index):
        cluster_mapping[cluster_id] = i
    
    # Generate dynamic cluster descriptions based on number of clusters
    n_clusters = len(cluster_means)
    cluster_descriptions = generate_cluster_descriptions(n_clusters)
        
    df_clustered['cluster_named'] = df_clustered['cluster'].map(cluster_mapping)
    df_clustered['cluster_label'] = df_clustered['cluster_named'].map(cluster_descriptions)
    
    # Create the interactive plot
    fig = px.scatter(
        df_clustered.sample(min(2000, len(df_clustered))),  # Sample for performance
        x='log_listeners',
        y='log_genre_popularity',
        color='cluster_label',
        hover_name='artist_name',
        hover_data={
            'tag': True,
            'listeners': ':,',
            'log_listeners': False,
            'log_genre_popularity': False,
            'cluster_label': False
        },
        title="Artist Clusters: Popularity vs Genre Mainstream-ness",
        labels={
            'log_listeners': 'Artist Popularity (log scale)',
            'log_genre_popularity': 'Genre Popularity (log scale)',
            'cluster_label': 'Cluster'
        },
        template='plotly_dark',
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    fig.update_layout(
        height=600,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig


def analyze_clusters(df_clustered):
    """
    Generate insights about the clusters.
    """
    insights = []
    
    # Sort clusters by average listener count for consistent naming
    cluster_means = df_clustered.groupby('cluster')['log_listeners'].mean().sort_values(ascending=False)
    cluster_mapping = {}
    for i, cluster_id in enumerate(cluster_means.index):
        cluster_mapping[cluster_id] = i
    
    # Generate dynamic cluster descriptions based on number of clusters
    n_clusters = len(cluster_means)
    cluster_descriptions = generate_cluster_descriptions(n_clusters)
    
    for cluster_id in sorted(df_clustered['cluster'].unique()):
        cluster_data = df_clustered[df_clustered['cluster'] == cluster_id]
        
        avg_listeners = cluster_data['listeners'].mean()
        top_genres = cluster_data['tag'].value_counts().head(3)
        artist_count = len(cluster_data)
        
        # Map to descriptive name
        named_cluster_id = cluster_mapping.get(cluster_id, cluster_id)
        cluster_name = cluster_descriptions.get(named_cluster_id, f"Cluster {cluster_id}")
        
        insights.append({
            'cluster': cluster_name,
            'avg_listeners': f"{avg_listeners:,.0f}",
            'artist_count': artist_count,
            'top_genres': list(top_genres.index),
            'example_artists': list(cluster_data['artist_name'].sample(min(3, len(cluster_data))))
        })
    
    return insights


def generate_cluster_descriptions(n_clusters):
    """
    Generate appropriate cluster descriptions based on the number of clusters.
    """
    if n_clusters == 3:
        return {
            0: "Mainstream Artists",
            1: "Mid-tier Artists", 
            2: "Underground Artists"
        }
    elif n_clusters == 4:
        return {
            0: "Mainstream Giants",
            1: "Popular Artists",
            2: "Emerging Artists",
            3: "Underground Artists"
        }
    elif n_clusters == 5:
        return {
            0: "Mainstream Giants",
            1: "Popular Acts", 
            2: "Mid-tier Artists",
            3: "Underground Favorites",
            4: "Deep Underground"
        }
    elif n_clusters == 6:
        return {
            0: "Mainstream Giants",
            1: "Popular Acts",
            2: "Well-known Artists",
            3: "Mid-tier Artists",
            4: "Underground Favorites",
            5: "Deep Underground"
        }
    elif n_clusters == 7:
        return {
            0: "Mainstream Giants",
            1: "Popular Acts",
            2: "Well-known Artists",
            3: "Mid-tier Artists",
            4: "Emerging Artists",
            5: "Underground Favorites",
            6: "Deep Underground"
        }
    else:
        # Fallback for any other number
        return {i: f"Cluster {i+1}" for i in range(n_clusters)}


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

# Create tabs
tab1, tab2 = st.tabs(["🎯 Get Recommendations", "🔍 Explore Artist Clusters"])

with tab1:
    # Add informational note about the algorithm
    st.info("""
    **🎯 How "Underground" is Defined:**
    - Artists must have at least **1,000 total listeners** (ensures they're discoverable on streaming platforms)
    - "Underground" = artists below the **75th percentile** of listener counts within their genre
    - The "adventurous" slider controls the mix between familiar similar artists and these underground discoveries
    """)
    
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

with tab2:
    st.header("🔍 Explore Artist Clusters")
    st.write("Discover how artists group together based on their popularity and genre characteristics using machine learning clustering.")
    
    if artist_df is not None:
        # Prepare clustering data
        with st.spinner("Preparing artist data for clustering..."):
            df_clustering, features = prepare_clustering_data(artist_df)
            
        # User controls for clustering
        col1, col2 = st.columns([1, 3])
        
        with col1:
            n_clusters = st.selectbox(
                "Number of clusters:",
                options=[3, 4, 5, 6, 7],
                index=2,  # Default to 5
                help="Choose how many artist groups you want to see"
            )
            
            st.info("**Features used:**\n- Artist popularity (log scale)\n- Genre mainstream-ness")
        
        # Perform clustering
        with st.spinner("Running K-means clustering..."):
            df_clustered, kmeans, scaler = perform_clustering(df_clustering, features, n_clusters)
            
        # Display cluster insights
        with col2:
            insights = analyze_clusters(df_clustered)
            
            st.subheader("📊 Cluster Summary")
            for insight in insights:
                with st.expander(f"🎯 {insight['cluster']} ({insight['artist_count']} artists)"):
                    st.write(f"**Average Listeners:** {insight['avg_listeners']}")
                    st.write(f"**Top Genres:** {', '.join(insight['top_genres'][:3])}")
                    st.write(f"**Example Artists:** {', '.join(insight['example_artists'])}")
        
        # Create and display the visualization
        st.subheader("Interactive Cluster Visualization")
        cluster_fig = create_cluster_visualization(df_clustered)
        st.plotly_chart(cluster_fig, use_container_width=True)
        
        st.markdown("""
        ### 🤖 How This Works
        This visualization uses **K-means clustering**, a machine learning algorithm that groups artists based on:
        - **Artist Popularity (X-axis):** How many total listeners the artist has (log scale)
        - **Genre Mainstream-ness (Y-axis):** How popular their primary genre is overall
        
        Each point represents an artist, and the colors show which cluster they belong to. 
        Hover over points to see artist details!
        """)
        
    else:
        st.error("Could not load artist data for clustering analysis.") 