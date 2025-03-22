import requests
import json
import os
import base64
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('spotify_fetch')

def get_spotify_token(client_id, client_secret):
    """
    Get Spotify access token using Client Credentials flow.
    This only works for endpoints that don't require user authentication.
    """
    logger.info("Getting Spotify access token")
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        json_result = response.json()
        logger.info("Successfully obtained Spotify access token")
        return json_result["access_token"]
    except Exception as e:
        logger.error(f"Error getting Spotify token: {str(e)}")
        if hasattr(response, 'text'):
            logger.error(f"Response: {response.text}")
        raise

def get_podcast_episodes(client_id, client_secret, show_id):
    """
    Get all episodes for a Spotify podcast using show ID.
    """
    token = get_spotify_token(client_id, client_secret)
    logger.info(f"Fetching episodes for Spotify show ID: {show_id}")
    
    # Initialize variables
    episodes = []
    offset = 0
    limit = 50  # Spotify's max limit per request
    
    # Make multiple requests to get all episodes
    while True:
        url = f"https://api.spotify.com/v1/shows/{show_id}/episodes"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        params = {
            "limit": limit,
            "offset": offset,
            "market": "DE"  # Assuming German market for Die Sogenannte Gegenwart
        }
        
        try:
            logger.info(f"Making Spotify API request with offset {offset}")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Get episode data
            new_episodes = []
            for episode in data.get('items', []):
                episode_id = episode.get('id')
                episode_name = episode.get('name')
                release_date = episode.get('release_date')
                external_urls = episode.get('external_urls', {})
                spotify_url = external_urls.get('spotify')
                
                new_episodes.append({
                    "title": episode_name,
                    "url": spotify_url,
                    "episode_id": episode_id,
                    "release_date": release_date,
                    "source": "spotify"
                })
            
            logger.info(f"Retrieved {len(new_episodes)} episodes (offset {offset})")
            
            # Add to total episodes list
            episodes.extend(new_episodes)
            
            # Check if we need to make another request
            if len(new_episodes) < limit or not data.get('next'):
                logger.info(f"No more episodes to fetch, total episodes: {len(episodes)}")
                break
            
            offset += limit
            
        except Exception as e:
            logger.error(f"Error fetching Spotify episodes: {str(e)}")
            if hasattr(response, 'text'):
                logger.error(f"Response: {response.text}")
            break
    
    return episodes

def save_episodes(episodes, output_file):
    """
    Save episodes to a JSON file
    """
    try:
        logger.info(f"Saving {len(episodes)} episodes to {output_file}")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(episodes, f, indent=2)
        logger.info(f"Successfully saved episodes to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error saving episodes: {str(e)}")
        return False

def main():
    """
    Main function to fetch Spotify podcast episodes
    """
    # Get credentials from environment variables
    client_id = os.environ.get('SPOTIFY_CLIENT_ID')
    client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
    show_id = os.environ.get('SPOTIFY_SHOW_ID', '28XdO4hmYjzx83Ct7PeENb')  # Die sogenannte Gegenwart show ID
    
    if not client_id or not client_secret:
        logger.error("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables are required")
        exit(1)
    
    # Fetch episodes
    episodes = get_podcast_episodes(client_id, client_secret, show_id)
    
    # Save to file
    if episodes:
        output_file = os.environ.get('SPOTIFY_OUTPUT_FILE', 'data/episodes/spotify_episode_links.json')
        save_episodes(episodes, output_file)
        
        # Set output for GitHub Actions
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"spotify_episode_links={json.dumps(episodes)}\n")
                f.write(f"spotify_episode_count={len(episodes)}\n")
        
        logger.info(f"Successfully processed {len(episodes)} Spotify episodes")
        print(f"Found {len(episodes)} episodes on Spotify:")
        for ep in episodes[:10]:  # Print first 10 episodes for brevity
            print(f"- {ep['title']}: {ep['url']}")
        if len(episodes) > 10:
            print("...and more")
    else:
        logger.warning("No episodes were found or an error occurred")

if __name__ == "__main__":
    main()
