# Gegenwartscheck Transcript Analyzer

A tool to automatically extract and analyze transcripts from the "Gegenwartscheck" segments in the podcast "Dies sogenannte Gegenwart".

## About

This project automatically extracts transcripts from podcast episodes of the German podcast "Dies sogenannte Gegenwart" with a focus on the "Gegenwartscheck" game segments. The system fetches episodes from Apple Podcasts, extracts their transcripts, and uses Gemini AI to analyze the content and extract structured data about the game segments.

## How It Works

The system uses a series of GitHub Actions workflows to:

1. **Fetch episode links** - Gets links to podcast episodes from Apple Podcasts
2. **Process episodes** - Opens each episode in the macOS Podcasts app and views the transcript to cache it
3. **Extract transcripts** - Parses the cached TTML files to extract structured transcript data
4. **Analyze transcripts** - Uses the Gemini API to analyze the transcripts and extract structured data about the "Gegenwartscheck" segments
5. **Deploy website** - Deploys a GitHub Pages website to visualize the extracted data

## Data Structure

### Raw Transcripts

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

### Analyzed Data

Analyzed "Gegenwartscheck" data is stored in the `website/data/` directory with the following structure:

```json
{
  "episode_title": "Episode Title",
  "podcast_id": "12345",
  "episode_date": "2023-01-01",
  "extracted_date": "2023-01-05T12:00:00",
  "gegenwartsvorschlaege": [
    {
      "vorschlag": "Name des Gegenwartsvorschlags",
      "vorschlagender": "Nina/Lars/Ijoma/[Name des Hörers]",
      "ist_hoerer": true/false,
      "hoerer_name": "Name des Hörers (falls vorhanden)",
      "begruendung": "Begründung für den Vorschlag",
      "metaebene": "Metaebene (falls explizit erwähnt)",
      "punkt_erhalten": true/false,
      "punkt_von": "Nina/Lars/Ijoma",
      "tags": ["Tag1", "Tag2", "Tag3"]
    }
  ]
}
```

## Development

See the technical specification documents in the `specs/` directory for implementation details:
- [Workflow Design](specs/workflow_design.md)
- [Gemini Analyzer](specs/gemini_analyzer.md)

### Running Workflows

The workflows can be triggered manually or run on a schedule:

1. **Get Podcast Episode Links** (`get-podcast-links.yml`) - Runs weekly by default
2. **Process Episodes** (`process-episodes.yml`) - Triggered automatically by the previous workflow
3. **Extract Transcript** (`extract-transcript.yml`) - Triggered for each episode by the process workflow
4. **Gemini Analyzer** (`gemini-analyzer.yml`) - Triggered after new transcripts are extracted or manually

### Requirements

To run the Gemini analyzer, you need:

1. A Gemini API key stored as a GitHub Secret named `GEMINI_API_KEY`
2. Python 3.10 or higher

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- "Dies sogenannte Gegenwart" podcast for the content
- Apple Podcasts for providing transcripts
- Google's Gemini API for semantic analysis
- Based on transcript extraction techniques from [apple-podcast-transcript-viewer](https://github.com/dado3212/apple-podcast-transcripts)