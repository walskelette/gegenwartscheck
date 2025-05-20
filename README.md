# Podcast Analysis and "Gegenwartsvorschläge" Viewer

This project automates the process of fetching podcast episodes, extracting transcripts, analyzing them for "Gegenwartsvorschläge" (suggestions of contemporary phenomena) using Gemini, and presenting these suggestions on a searchable static website.

## Project Overview

The core idea is to analyze episodes of the podcast "Die sogenannte Gegenwart" (or any other podcast with a similar format if adapted) to identify and catalogue the "Gegenwartsvorschläge" discussed by the hosts. These suggestions, along with their context and whether they received a "point," are then made available through a GitHub Pages website.

## Data Pipeline

The data pipeline consists of several automated and manually triggered steps, primarily managed through GitHub Actions workflows:

1.  **Fetch Episode Links (`get-podcast-links.yml`):**
    *   Runs weekly and can be manually dispatched.
    *   Fetches episode lists from Apple Podcasts and Spotify using `scripts/spotify_fetch.py` for Spotify data.
    *   Merges these lists, removing duplicates based on release date, and saves the combined list to `data/episodes/episode_links.json`.

2.  **Process Episodes & Cache Transcripts (`process-episodes.yml`):**
    *   Manually dispatched workflow.
    *   Takes episode URLs from `data/episodes/episode_links.json`.
    *   Uses `osascript` on a macOS runner to interact with the Apple Podcasts desktop application.
    *   For each episode, it navigates to the episode, shows the transcript, and then zips the application's cache directory (which contains the TTML transcript data).
    *   Saves these zipped cache files to `data/raw/<primary_id>_cache.zip`, where `primary_id` is usually the Apple Podcast ID or Spotify ID.

3.  **Extract Transcripts (`extract-transcript.yml`):**
    *   Manually dispatched workflow.
    *   Processes the `_cache.zip` files from `data/raw/`.
    *   Unzips the archives and extracts the transcript text from the TTML files found within.
    *   Saves the cleaned transcript data (including speaker information and timestamps) as JSON files in `data/transcripts/<primary_id>_transcript.json`.

4.  **Analyze Transcripts (`gemini-analyzer.yml` - `analyze` job):**
    *   Manually dispatched workflow.
    *   Uses `scripts/gemini_analyzer.py` to process transcripts from `data/transcripts/`.
    *   For each transcript, it calls the Gemini API to:
        *   Identify "Gegenwartsvorschläge."
        *   Extract details for each suggestion (proposer, reasoning, tags, whether a point was awarded, etc.).
        *   Perform a proofreading and correction step on the extracted data.
    *   Saves the structured analysis results as JSON files in `data/analyses/<primary_id>.json`.

5.  **Aggregate Data & Deploy Site (`gemini-analyzer.yml` - `build-and-deploy-site` job):**
    *   This job runs automatically after the `analyze` job in the `gemini-analyzer.yml` workflow.
    *   Uses `scripts/aggregate_data.py` to:
        *   Read all individual analysis files from `data/analyses/`.
        *   Combine them with episode metadata from `data/episodes/episode_links.json`.
        *   Produce a single JSON file: `docs/site_data.json`.
    *   Commits the updated `docs/site_data.json` to the repository.
    *   Deploys the content of the `/docs` directory (which includes `index.html`, `style.css`, `main.js`, and `site_data.json`) to GitHub Pages.

## GitHub Pages Site

The static website provides a user-friendly interface to explore the "Gegenwartsvorschläge":

*   **Searchable List:** Allows users to search suggestions by keywords, proposer, or tags.
*   **Statistics:** Displays interesting statistics, such as the number of suggestions per host, success rates, and popular tags.
*   **Direct Links:** Provides links to the original podcast episodes on Apple Podcasts and Spotify where available.

The site is automatically updated whenever new analyses are processed and committed via the `gemini-analyzer.yml` workflow.

## Key Scripts

*   **`scripts/spotify_fetch.py`**: Fetches episode data from the Spotify API.
*   **`scripts/gemini_analyzer.py`**: Analyzes transcripts using the Gemini API to extract "Gegenwartsvorschläge".
*   **`scripts/aggregate_data.py`**: Consolidates all analysis results and episode metadata into a single file for the web application.

## Manual Workflow Triggers

Most data processing workflows (`process-episodes`, `extract-transcript`, `gemini-analyzer`) are manually triggered via the GitHub Actions UI. This allows for controlled processing and reprocessing if needed.
The `get-podcast-links` workflow runs on a weekly schedule but can also be manually triggered.
The deployment of the GitHub Pages site is automated as part of the `gemini-analyzer` workflow.
