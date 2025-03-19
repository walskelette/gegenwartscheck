# GegenwartsCheck Project Specifications

## Project Overview
GegenwartsCheck is a tool for analyzing transcripts using AI models (currently Google's Gemini) to extract insights and perform various analyses. The system processes transcript files and generates analysis output files.

## Directory Structure
- `data/` - Contains all data files
  - `transcripts/` - Contains raw transcript JSON files
  - `analyses/` - Contains generated analysis JSON files
- `llm_context/` - Contains documentation, specs, and TODO items
- `.github/workflows/` - Contains GitHub Actions workflow files

## Workflow Process
1. The GitHub Actions workflow (`gemini-analyzer.yml`) is triggered manually
2. The workflow:
   - Sets up Python environment
   - Installs required dependencies
   - Creates an output directory (if not exists)
   - Processes each transcript file using the Gemini API
   - Commits the processed data back to the repository

## File Formats
### Transcript Files
- Format: JSON
- Naming convention: `[ID]_transcript.json`
- Contains raw transcript data

### Analysis Files
- Format: JSON
- Naming convention: `[ID]_gegenwartscheck.json`
- Contains analysis results from the Gemini API

## Future Enhancements
- UI for visualization of analysis results
- Additional analysis types
- Testing framework
- Improved error handling 