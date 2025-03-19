# GegenwartsCheck Project Specifications

## Project Overview
GegenwartsCheck is a tool for analyzing transcripts from the German podcast "Die sogenannte Gegenwart" using Google's Gemini AI model. The system processes transcript files and generates structured analysis output files that capture the "Gegenwartsvorschläge" (proposals for what is contemporary/current) made during the podcast episodes.

## Directory Structure
- `data/` - Contains all data files
  - `transcripts/` - Contains raw transcript JSON files
  - `analyses/` - Contains generated analysis JSON files
- `scripts/` - Contains Python scripts for processing data
  - `gemini_analyzer.py` - Main script for analyzing transcripts
  - `requirements.txt` - Dependencies for the scripts
- `.github/workflows/` - Contains GitHub Actions workflow files
  - `gemini-analyzer.yml` - Workflow for processing transcripts
- `llm_context/` - Contains documentation, specs, and TODO items
  - `TODO.md` - List of current and future tasks
  - `SPECS.md` - Project specifications and documentation

## Workflow Process
1. The GitHub Actions workflow (`gemini-analyzer.yml`) can be triggered in three ways:
   - Manually via `workflow_dispatch`
   - Automatically when new transcript files are pushed
   - After the "Extract Podcast Transcript" workflow completes
2. The workflow:
   - Sets up Python environment
   - Installs required dependencies
   - Creates an output directory (if not exists)
   - Processes each transcript file using the Gemini API
   - Commits the processed data back to the repository

## Gemini Analysis Process
1. The `gemini_analyzer.py` script:
   - Loads transcript files from the `data/transcripts` directory
   - Creates detailed prompts for the Gemini API
   - Makes API calls to Gemini with appropriate rate limiting (2 RPM)
   - Performs a two-stage analysis:
     - Initial extraction of "Gegenwartsvorschläge"
     - Secondary proofreading to correct potential errors
   - Generates structured JSON output
   - Saves results to the `data/analyses` directory

## File Formats

### Transcript Files
- Format: JSON
- Naming convention: `[ID]_transcript.json`
- Contains:
  - `episode_title`: Title of the podcast episode
  - `podcast_id`: Unique identifier for the podcast
  - `episode_id`: Unique identifier for the episode
  - `release_date`: Date the episode was released
  - `extracted_date`: Date the transcript was extracted
  - `transcript`: Array of transcript segments, each with:
    - `speaker`: Speaker identifier (e.g., "SPEAKER_1")
    - `text`: Transcribed text
    - `begin_time`: Timestamp for segment start
    - `end_time`: Timestamp for segment end
    - Additional timing information

### Analysis Files
- Format: JSON
- Naming convention: `[ID]_gegenwartscheck.json`
- Contains:
  - `episode_title`: Title of the podcast episode
  - `podcast_id`: Unique identifier for the podcast
  - `episode_id`: Unique identifier for the episode
  - `episode_date`: Date of the episode
  - `extracted_date`: Date the analysis was performed
  - `gegenwartsvorschlaege`: Array of proposals, each with:
    - `vorschlag`: The proposed concept/term
    - `vorschlagender`: Person who made the proposal
    - `ist_hoerer`: Boolean indicating if proposer is a listener
    - `hoerer_name`: Name of listener (if applicable)
    - `begruendung`: Justification for the proposal
    - `metaebene`: Meta-level context (if mentioned)
    - `punkt_erhalten`: Boolean indicating if proposal received a point
    - `punkt_von`: Person who awarded the point
    - `tags`: Array of thematic tags
    - `start_zeit`: Timestamp when the proposal starts
    - `ende_zeit`: Timestamp when the proposal ends

## API Usage
- The project uses Google's Gemini API (requires API key)
- Configured models:
  - `gemini-2.0-flash-thinking-exp-01-21` - For initial analysis
  - `gemini-2.0-pro-exp-02-05` - For proofreading
- Rate limits are respected (2 RPM) with retry mechanisms

## Future Enhancements
- Web UI for visualization of analysis results
- More sophisticated analysis capabilities
- Testing framework
- Improved documentation
- Monitoring and logging 