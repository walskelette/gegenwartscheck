# Gegenwartscheck Transcript Analyzer

A tool to automatically extract and analyze transcripts from the "Gegenwartscheck" segments in the podcast "Dies sogenannte Gegenwart".

## About

This project automatically extracts transcripts from podcast episodes of the German podcast "Dies sogenannte Gegenwart" with a focus on the "Gegenwartscheck" game segments. The system fetches episodes from Apple Podcasts, extracts their transcripts, and stores them in a structured format for further analysis.

## How It Works

The system uses a series of GitHub Actions workflows to:

1. **Fetch episode links** - Gets links to podcast episodes from Apple Podcasts
2. **Process episodes** - Opens each episode in the macOS Podcasts app and views the transcript to cache it
3. **Extract transcripts** - Parses the cached TTML files to extract structured transcript data
4. **Store data** - Saves the transcripts as JSON files in the data directory

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

### Running Workflows

The workflows can be triggered manually or run on a schedule:

1. **Get Podcast Episode Links** (`get-podcast-links.yml`) - Runs weekly by default
2. **Process Episodes** (`process-episodes.yml`) - Triggered automatically by the previous workflow
3. **Extract Transcript** (`extract-transcript.yml`) - Triggered for each episode by the process workflow

### Future Development

Planned enhancements for this project include:

1. Creating a GitHub Pages website to visualize the transcript data
2. Implementing analysis to extract Gegenwartscheck game information
3. Adding error recovery mechanisms for workflow failures
4. Optimizing AppleScript interactions for better reliability

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- "Dies sogenannte Gegenwart" podcast for the content
- Apple Podcasts for providing transcripts
- Based on transcript extraction techniques from [apple-podcast-transcript-viewer](https://github.com/dado3212/apple-podcast-transcripts)