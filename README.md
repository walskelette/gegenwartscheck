# Gegenwartscheck Transcript Analyzer

A tool to analyze transcripts from the "Gegenwartscheck" segments in the podcast "Dies sogenannte Gegenwart".

## About

This project automatically extracts and analyzes transcripts from the "Gegenwartscheck" game segments in the German podcast "Dies sogenannte Gegenwart". The system fetches episodes from Apple Podcasts, extracts their transcripts, and publishes the analyzed data to GitHub Pages.

## How It Works

The system uses a series of GitHub Actions workflows to:

1. **Fetch episode links** - Gets links to podcast episodes containing "Gegenwartscheck" segments from Apple Podcasts
2. **Process episodes** - Opens each episode in the macOS Podcasts app and views the transcript to cache it
3. **Extract transcripts** - Parses the cached TTML files to extract structured transcript data
4. **Analyze content** - (Coming soon) Analyzes the transcript to extract Gegenwartscheck game data
5. **Publish results** - (Coming soon) Deploys the analyzed data to GitHub Pages

## Data Structure

Extracted transcripts are stored in the `data/` directory as JSON files with the following structure:

```json
{
  "episode_title": "Episode Title",
  "podcast_id": "12345",
  "extracted_date": "2023-01-01T12:00:00",
  "transcript": [
    {
      "speaker": "Speaker Name",
      "text": "Spoken text content..."
    }
  ]
}
```

## Development

See the [workflow design document](specs/workflow_design.md) for technical implementation details.

### Running Locally

To run the transcript extraction and analysis locally:

1. Install dependencies: `pip install requests lxml beautifulsoup4`
2. Get episode links: `python scripts/get_episodes.py`
3. Extract transcripts from Apple Podcasts (macOS only)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- "Dies sogenannte Gegenwart" podcast for the content
- Apple Podcasts for providing transcripts
- Based on [apple-podcast-transcript-viewer](https://github.com/dado3212/apple-podcast-transcripts)