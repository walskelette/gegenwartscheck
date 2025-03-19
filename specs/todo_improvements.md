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

3. ~~**Add Timestamps to Transcripts**~~
   - ~~Modify transcript extraction to include timestamps for each section~~
   - ~~This will enable future linking to specific time points in episodes~~
   - **Completed**: Timestamp extraction has been implemented in the transcript extraction workflow, and the structure supports begin_time, end_time, and duration_seconds fields for each transcript chunk when available.

4. ~~**Update Gemini Prompts for Timestamp Offsets**~~
   - ~~Update the Gemini prompts to include an offset field in seconds~~
   - ~~Modify the analyzer script to capture and include this information in the output~~
   - **Completed**: Gemini prompts have been updated to include timestamp information in both input and output. The timestamp fields are now available in the analysis output as start_zeit and ende_zeit.

5. ~~**Implement Second-Pass Analysis with Gemini Pro**~~
   - ~~Add a proofreading step using the Gemini Pro model~~
   - ~~Correct spelling, terminology, and concept names~~
   - ~~Ensure transcription accuracy without changing content meaning~~
   - **Completed**: Added a second-pass analysis using Gemini Pro that proofreads and improves the initial analysis results, focusing on spelling corrections, accuracy improvements, and tag refinement.

6. ~~**Implement Google Grounding for Improved Accuracy**~~
   - ~~Integrate Google's grounding feature to improve the accuracy of Gemini's responses~~
   - ~~Use the provided code as a reference for implementation~~
   - **Completed**: Implemented Google Grounding feature by enabling the google_search_retrieval tool in both the initial analysis and proofreading steps to improve the accuracy of Gemini's responses with factual information from the internet.

7. **Remove test_gemini.py File**
   - Remove the test_gemini.py file as it's no longer needed
   - Ensure this doesn't break any functionality or dependencies
   - This will clean up the codebase and remove unused test code

8. **Fix Episode Count Issue**
   - Currently only 4 transcripts are pulled despite restricting to 5 episodes
   - Investigate if the first result in the Apple link result list is metadata about the whole show
   - Modify the code to ensure it correctly processes the intended number of episodes
   - Test to verify that 5 actual episode transcripts are now processed

9. **Improve Second Pass (Proofreading) Prompt**
   - Enhance the second pass prompt to explicitly explain that this is an auto-generated transcript of a German language podcast
   - Add emphasis that foreign words and loanwords (Fremd/Lehnwörter) from other languages might be especially vulnerable to misspellings
   - Remove ALL examples in the prompts, as they are based on previously generated data that doesn't meet quality standards
   - Test the improved prompt thoroughly to ensure better handling of transcription errors

## Implementation Strategy

Each TODO will be implemented one at a time, with thorough testing after each step:

1. Implement the change
2. Commit and push the code
3. Wait for the GitHub Action to run and complete
4. Check the results for correctness
5. If issues are found, fix and repeat the process
6. Once working correctly, move to the next TODO item

## Current Status

TODOs #1 through #6 have been completed successfully. We are now working on TODOs #7 through #9:

1. ✅ Using Episode IDs for file naming
2. ✅ Including episode upload/release dates
3. ✅ Adding timestamps to transcripts
4. ✅ Updating Gemini prompts for timestamp offsets
5. ✅ Implementing second-pass analysis with Gemini Pro
6. ✅ Implementing Google Grounding for improved accuracy
7. ⏳ Remove test_gemini.py file
8. ⏳ Fix episode count issue
9. ⏳ Improve second pass prompt 