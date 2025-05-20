import json
import os
import glob
import logging
import argparse
from typing import List, Dict, Any, Optional

# 1. Constants
ANALYSES_DIR = "data/analyses"
EPISODE_LINKS_FILE = "data/episodes/episode_links.json"
OUTPUT_DIR = "docs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "site_data.json")

# 2. Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_episode_links(filepath: str) -> Dict[str, Dict[str, Any]]:
    """
    Loads episode links from a JSON file and creates a lookup dictionary.
    Keys are apple_id (str) and spotify_id.
    """
    episode_lookup: Dict[str, Dict[str, Any]] = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            episodes_data = json.load(f)
        
        for episode in episodes_data:
            if not isinstance(episode, dict):
                logging.warning(f"Skipping non-dictionary item in episode links: {episode}")
                continue

            apple_id = episode.get('apple_id')
            spotify_id = episode.get('spotify_id')

            if apple_id:
                episode_lookup[str(apple_id)] = episode
            if spotify_id:
                episode_lookup[spotify_id] = episode
        
        logging.info(f"Loaded {len(episodes_data)} episodes from {filepath}, created {len(episode_lookup)} lookup entries.")
    except FileNotFoundError:
        logging.error(f"Episode links file not found: {filepath}")
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from episode links file: {filepath}")
    return episode_lookup

def process_analyses(analyses_dir: str, episode_lookup: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Processes analysis files, enriches Vorschlaege with episode metadata.
    """
    all_vorschlaege: List[Dict[str, Any]] = []
    analysis_files = glob.glob(os.path.join(analyses_dir, "*.json"))

    if not analysis_files:
        logging.warning(f"No analysis files found in directory: {analyses_dir}")
        return all_vorschlaege

    for file_path in analysis_files:
        logging.info(f"Processing analysis file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)

            if not isinstance(analysis_data, dict):
                logging.warning(f"Skipping malformed analysis file (not a dict): {file_path}")
                continue

            # Extract IDs and details from analysis file content
            filename_primary_id = analysis_data.get('filename_primary_id') # This should be the primary key from the filename
            analysis_apple_id = str(analysis_data.get('apple_id', ''))
            analysis_spotify_id = analysis_data.get('spotify_id', '')
            episode_title_from_analysis = analysis_data.get('episode_title', 'Unknown Title')
            episode_date_from_analysis = analysis_data.get('episode_date', 'Unknown Date')

            # Determine the best ID to use for lookup in episode_links.json
            # The filename_primary_id (derived from the original zip) is usually the most reliable.
            lookup_id = filename_primary_id or analysis_apple_id or analysis_spotify_id
            
            episode_metadata: Optional[Dict[str, Any]] = None
            if lookup_id:
                episode_metadata = episode_lookup.get(str(lookup_id))
                if not episode_metadata and analysis_apple_id and analysis_apple_id != lookup_id: # Try apple_id if primary lookup failed
                    episode_metadata = episode_lookup.get(analysis_apple_id)
                if not episode_metadata and analysis_spotify_id and analysis_spotify_id != lookup_id: # Try spotify_id if primary lookup failed
                    episode_metadata = episode_lookup.get(analysis_spotify_id)
            
            if not episode_metadata:
                logging.warning(f"No episode metadata found in lookup for ID '{lookup_id}' from file {file_path}")

            for i, vorschlag_item in enumerate(analysis_data.get('gegenwartsvorschlaege', [])):
                if not isinstance(vorschlag_item, dict):
                    logging.warning(f"Skipping malformed vorschlag_item (not a dict) in {file_path}")
                    continue

                enriched_vorschlag = {**vorschlag_item} # Copy original fields

                # Add/overwrite with episode-level information
                enriched_vorschlag['episode_title_from_analysis'] = episode_title_from_analysis
                enriched_vorschlag['episode_date_from_analysis'] = episode_date_from_analysis
                enriched_vorschlag['episode_apple_id_from_analysis'] = analysis_apple_id
                enriched_vorschlag['episode_spotify_id_from_analysis'] = analysis_spotify_id
                enriched_vorschlag['episode_filename_primary_id'] = filename_primary_id
                
                # Create a unique ID for the Vorschlag
                enriched_vorschlag['unique_vorschlag_id'] = f"{filename_primary_id or 'unknown_episode'}_{i}"


                if episode_metadata:
                    enriched_vorschlag['episode_title'] = episode_metadata.get('title', episode_title_from_analysis)
                    enriched_vorschlag['episode_date'] = episode_metadata.get('release_date', episode_date_from_analysis)
                    enriched_vorschlag['episode_apple_url'] = episode_metadata.get('apple_url') # Assuming 'apple_url' exists in links
                    enriched_vorschlag['episode_spotify_url'] = episode_metadata.get('url') # 'url' is spotify URL in combined links
                    enriched_vorschlag['episode_apple_id'] = str(episode_metadata.get('apple_id', analysis_apple_id))
                    enriched_vorschlag['episode_spotify_id'] = episode_metadata.get('spotify_id', analysis_spotify_id)
                else:
                    enriched_vorschlag['episode_title'] = episode_title_from_analysis
                    enriched_vorschlag['episode_date'] = episode_date_from_analysis
                    enriched_vorschlag['episode_apple_url'] = None
                    enriched_vorschlag['episode_spotify_url'] = None
                    enriched_vorschlag['episode_apple_id'] = analysis_apple_id
                    enriched_vorschlag['episode_spotify_id'] = analysis_spotify_id

                # Ensure start_zeit_sekunden is an integer
                start_zeit_str = vorschlag_item.get('start_zeit')
                start_zeit_sekunden = None
                if start_zeit_str is not None:
                    try:
                        start_zeit_sekunden = int(str(start_zeit_str).replace('s', ''))
                    except ValueError:
                        logging.warning(f"Could not convert start_zeit '{start_zeit_str}' to int for a vorschlag in {file_path}")
                enriched_vorschlag['start_zeit_sekunden'] = start_zeit_sekunden
                
                all_vorschlaege.append(enriched_vorschlag)

        except FileNotFoundError:
            logging.error(f"Analysis file not found during processing: {file_path}")
        except json.JSONDecodeError:
            logging.error(f"Error decoding JSON from analysis file: {file_path}")
        except Exception as e:
            logging.error(f"Unexpected error processing file {file_path}: {e}")

    logging.info(f"Processed {len(all_vorschlaege)} Vorschlaege from {len(analysis_files)} analysis files.")
    return all_vorschlaege

def save_output(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves the aggregated data to a JSON file.
    """
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir: # Ensure output_dir is not an empty string if output_path is just a filename
             os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Successfully saved aggregated data to: {output_path}")
    except OSError as e:
        logging.error(f"OSError when creating directories or writing file {output_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error saving output to {output_path}: {e}")

# 3. Main Function
def main(args):
    """
    Main function to orchestrate loading, processing, and saving of data.
    """
    logging.info("Starting data aggregation process...")
    
    episode_lookup = load_episode_links(args.episode_links_file)
    
    if not episode_lookup:
        logging.warning("Episode lookup is empty. Aggregation might be incomplete.")
        # Decide if to proceed or exit. For now, proceed.
        
    all_vorschlaege_data = process_analyses(args.analyses_dir, episode_lookup)
    
    if not all_vorschlaege_data:
        logging.warning("No Vorschlaege were processed. Output file will be empty or not created if saving empty is handled.")
        # Depending on requirements, you might want to avoid saving an empty list
    
    save_output(all_vorschlaege_data, args.output_file)
    
    logging.info("Data aggregation process finished.")

# 7. Script Execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aggregates podcast analysis data for website.")
    parser.add_argument("--analyses-dir", default=ANALYSES_DIR,
                        help=f"Directory containing analysis JSON files (default: {ANALYSES_DIR})")
    parser.add_argument("--episode-links-file", default=EPISODE_LINKS_FILE,
                        help=f"Path to the episode links JSON file (default: {EPISODE_LINKS_FILE})")
    parser.add_argument("--output-file", default=OUTPUT_FILE,
                        help=f"Path to the output aggregated JSON file (default: {OUTPUT_FILE})")
    
    args = parser.parse_args()
    main(args)
