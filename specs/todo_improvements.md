# Gegenwartscheck Improvements TODO List

This document outlines the planned improvements to the Gegenwartscheck podcast analysis system.

## TODOs

1. ~~**Use Episode IDs for File Naming**~~
   - ~~Change file naming convention to use episode IDs instead of episode titles~~
   - ~~Update all relevant scripts and workflows~~
   - ~~This will make file handling more consistent and avoid issues with special characters in titles~~
   - **Completed**: All workflows now use episode IDs for file naming, with fallback to title-based naming for backward compatibility.

2. ~~**Include Episode Upload Date**~~
   - ~~Replace the current parse date with the actual episode upload date in the final data~~
   - ~~Modify the extraction and processing scripts to capture and use this information~~
   - **Completed**: Episode release date is now retrieved from the API and included in both transcripts and analyses.

3. **Add Timestamps to Transcripts**
   - Modify transcript extraction to include timestamps for each section
   - This will enable future linking to specific time points in episodes

4. **Update Gemini Prompts for Timestamp Offsets**
   - Update the Gemini prompts to include an offset field in seconds
   - Modify the analyzer script to capture and include this information in the output

5. **Implement Second-Pass Analysis with Gemini Pro**
   - Add a proofreading step using the Gemini Pro model
   - Correct spelling, terminology, and concept names
   - Ensure transcription accuracy without changing content meaning

6. **Implement Google Grounding for Improved Accuracy**
   - Integrate Google's grounding feature to improve the accuracy of Gemini's responses
   - Use the provided code as a reference for implementation

## Implementation Strategy

Each TODO will be implemented one at a time, with thorough testing after each step:

1. Implement the change
2. Commit and push the code
3. Wait for the GitHub Action to run and complete
4. Check the results for correctness
5. If issues are found, fix and repeat the process
6. Once working correctly, move to the next TODO item

## Current Status

TODOs #1 and #2 have been completed. Next, we will implement TODO #3: Add Timestamps to Transcripts. 