import unittest
from unittest.mock import patch, mock_open, MagicMock, call
import json
import os
import sys
from datetime import datetime

# Add scripts directory to sys.path to allow importing gemini_analyzer
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

from gemini_analyzer import (
    load_transcript,
    create_gemini_prompt,
    analyze_transcript_with_gemini,
    proofread_analysis_with_gemini,
    create_output_data,
    get_output_filename,
    validate_output_schema,
    extract_date_from_title, # Helper for create_output_data
    setup_gemini_client # To mock its behavior if needed for client creation
)

# Sample Data for Tests
sample_transcript_data = {
    "episode_title": "Test Episode Title",
    "apple_id": "12345apple",
    "spotify_id": "67890spotify",
    "filename_primary_id": "12345apple",
    "release_date": "2023-01-15",
    "transcript": [
        {"speaker": "SPEAKER_01", "text": "Lars speaking.", "begin_seconds": 5},
        {"speaker": "SPEAKER_00", "text": "Ijoma proposing something.", "begin_seconds": 10}
    ]
}

sample_initial_analysis_result = {
    "gegenwartsvorschlaege": [
        {
            "vorschlag": "Das Test-Phänomen",
            "vorschlagender": "Ijoma",
            "ist_hoerer": False,
            "hoerer_name": None,
            "begruendung": "Eine Test Begründung.",
            "metaebene": None,
            "punkt_erhalten": True,
            "punkt_von": "Lars",
            "tags": ["test", "python"],
            "start_zeit": "10s"
        },
        {
            "vorschlag": "Listener Idea",
            "vorschlagender": "SPEAKER_01", # Not a host, should be defaulted
            "ist_hoerer": True,
            "hoerer_name": "A Listener",
            "begruendung": "Listener reasoning.",
            "tags": ["listener", "community"],
            "start_zeit": "120"
            # punkt_erhalten missing
            # punkt_von missing
        },
        {
            "vorschlag": "Old format",
            "vorschlagender": "Lars",
            "ist_hoerer": False,
            "hoerer_name": None,
            "begruendung": "Testing ende_zeit removal.",
            "metaebene": None,
            "punkt_erhalten": False,
            "punkt_von": "Ijoma",
            "tags": ["cleanup"],
            "start_zeit": "200s",
            "ende_zeit": "210s" # Should be removed
        }
    ]
}

class TestGeminiAnalyzerLogic(unittest.TestCase):

    # --- Tests for load_transcript ---
    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    def test_load_transcript_success(self, mock_file):
        expected_data = {"key": "value"}
        result = load_transcript("dummy/path.json")
        self.assertEqual(result, expected_data)
        mock_file.assert_called_once_with("dummy/path.json", 'r', encoding='utf-8')

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_transcript_file_not_found(self, mock_file):
        with self.assertRaises(FileNotFoundError):
            load_transcript("dummy/nonexistent.json")
        mock_file.assert_called_once_with("dummy/nonexistent.json", 'r', encoding='utf-8')

    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value", invalid_json}')
    def test_load_transcript_json_decode_error(self, mock_file):
        with self.assertRaises(json.JSONDecodeError):
            load_transcript("dummy/invalid.json")
        mock_file.assert_called_once_with("dummy/invalid.json", 'r', encoding='utf-8')

    # --- Tests for get_output_filename ---
    def test_get_output_filename_apple_id(self):
        self.assertEqual(get_output_filename("12345apple_transcript.json"), "12345apple.json")
        self.assertEqual(get_output_filename("/path/to/12345apple_transcript.json"), "12345apple.json")

    def test_get_output_filename_complex_id(self):
        self.assertEqual(get_output_filename("Some-Complex-ID_transcript.json"), "Some-Complex-ID.json")

    def test_get_output_filename_numeric_id(self):
        self.assertEqual(get_output_filename("numeric123_transcript.json"), "numeric123.json")
    
    def test_get_output_filename_alphanumeric_id_with_hyphens_and_underscores(self):
        self.assertEqual(get_output_filename("abc-123_XYZ-789_transcript.json"), "abc-123_XYZ-789.json")

    def test_get_output_filename_fallback(self):
        self.assertEqual(get_output_filename("no_match.json"), "no_match_gegenwartscheck.json")
        self.assertEqual(get_output_filename("another_transcript_but_no_match.txt"), "another_transcript_but_no_match_gegenwartscheck.txt")


    # --- Tests for validate_output_schema ---
    def test_validate_output_schema_valid(self):
        valid_data = {
            "episode_title": "Title",
            "apple_id": "apple123",
            "spotify_id": "spotify123",
            "episode_date": "2023-01-01",
            "gegenwartsvorschlaege": []
        }
        self.assertTrue(validate_output_schema(valid_data))

    def test_validate_output_schema_missing_field(self):
        invalid_data_missing_title = {
            "apple_id": "apple123",
            "spotify_id": "spotify123",
            "episode_date": "2023-01-01",
            "gegenwartsvorschlaege": []
        }
        with patch('logging.warning') as mock_log:
            self.assertFalse(validate_output_schema(invalid_data_missing_title))
            mock_log.assert_any_call("Fehlendes Feld im Output: episode_title")

        invalid_data_missing_vorschlaege = {
            "episode_title": "Title",
            "apple_id": "apple123",
            "spotify_id": "spotify123",
            "episode_date": "2023-01-01"
        }
        with patch('logging.warning') as mock_log:
            self.assertFalse(validate_output_schema(invalid_data_missing_vorschlaege))
            mock_log.assert_any_call("Fehlendes Feld im Output: gegenwartsvorschlaege")


    def test_validate_output_schema_vorschlaege_not_list(self):
        invalid_data = {
            "episode_title": "Title",
            "apple_id": "apple123",
            "spotify_id": "spotify123",
            "episode_date": "2023-01-01",
            "gegenwartsvorschlaege": "not a list"
        }
        with patch('logging.warning') as mock_log:
            self.assertFalse(validate_output_schema(invalid_data))
            mock_log.assert_any_call("'gegenwartsvorschlaege' ist nicht vom Typ Liste.")

    # --- Tests for create_gemini_prompt ---
    def test_create_gemini_prompt_basic_structure(self):
        prompt = create_gemini_prompt(sample_transcript_data)
        self.assertIn(sample_transcript_data["episode_title"], prompt)
        
        expected_transcript_segment1 = "SPEAKER_01: Lars speaking.\n\n"
        expected_transcript_segment2 = "SPEAKER_00: Ijoma proposing something.\n\n"
        self.assertIn(expected_transcript_segment1, prompt)
        self.assertIn(expected_transcript_segment2, prompt)
        
        # Check for key instructions in the prompt
        self.assertIn("Identifiziere alle \"Gegenwartsvorschläge\"", prompt)
        self.assertIn("Formatiere deine Antwort als JSON mit folgendem Schema:", prompt)
        self.assertIn("\"vorschlag\": \"Name des Vorschlags\"", prompt) # Example field
        self.assertIn("WICHTIG:", prompt)

    # --- Tests for create_output_data ---
    def test_create_output_data_basic_fields(self):
        output = create_output_data(sample_transcript_data, sample_initial_analysis_result)
        self.assertIsNotNone(output)
        self.assertEqual(output["episode_title"], sample_transcript_data["episode_title"])
        self.assertEqual(output["apple_id"], sample_transcript_data["apple_id"])
        self.assertEqual(output["spotify_id"], sample_transcript_data["spotify_id"])
        self.assertEqual(output["episode_date"], sample_transcript_data["release_date"])
        # filename_primary_id is NOT directly part of the output structure of create_output_data
        # it's used by the calling context (e.g. process_transcript) to determine the output filename

    def test_create_output_data_vorschlaege_processing(self):
        output = create_output_data(sample_transcript_data, sample_initial_analysis_result)
        self.assertIsNotNone(output)
        vorschlaege = output["gegenwartsvorschlaege"]
        
        # First vorschlag (explicit values)
        self.assertEqual(vorschlaege[0]["vorschlag"], "Das Test-Phänomen")
        self.assertEqual(vorschlaege[0]["vorschlagender"], "Ijoma")
        self.assertTrue(vorschlaege[0]["punkt_erhalten"])
        self.assertEqual(vorschlaege[0]["punkt_von"], "Lars")
        self.assertEqual(vorschlaege[0]["start_zeit"], "10") # 's' stripped

        # Second vorschlag (defaults and listener)
        self.assertEqual(vorschlaege[1]["vorschlag"], "Listener Idea")
        self.assertEqual(vorschlaege[1]["vorschlagender"], "Lars") # Defaulted for listener
        self.assertFalse(vorschlaege[1]["punkt_erhalten"]) # Defaulted
        self.assertIsNone(vorschlaege[1]["punkt_von"]) # Defaulted
        self.assertEqual(vorschlaege[1]["start_zeit"], "120")

        # Third vorschlag (ende_zeit removal)
        self.assertNotIn("ende_zeit", vorschlaege[2])
        self.assertEqual(vorschlaege[2]["start_zeit"], "200")


    @patch('gemini_analyzer.datetime')
    def test_create_output_data_date_handling(self, mock_datetime):
        # 1. Uses release_date if available
        transcript_with_release_date = {**sample_transcript_data, "release_date": "2024-03-10"}
        output = create_output_data(transcript_with_release_date, sample_initial_analysis_result)
        self.assertEqual(output["episode_date"], "2024-03-10")

        # 2. Uses upload_date if release_date is missing
        transcript_with_upload_date = {**sample_transcript_data, "release_date": None, "upload_date": "2024-03-11"}
        output = create_output_data(transcript_with_upload_date, sample_initial_analysis_result)
        self.assertEqual(output["episode_date"], "2024-03-11")

        # 3. Extracts from title if both are missing
        mock_datetime.now.return_value = datetime(2023, 7, 15) # For fallback if title has no date
        transcript_with_title_date = {**sample_transcript_data, "release_date": None, "upload_date": None, "episode_title": "Episode from 2022"}
        output = create_output_data(transcript_with_title_date, sample_initial_analysis_result)
        self.assertEqual(output["episode_date"], "2022-01-01") # extract_date_from_title logic

        # 4. Fallback to current date (mocked) if no date in title
        transcript_no_date_info = {**sample_transcript_data, "release_date": None, "upload_date": None, "episode_title": "Timeless Episode"}
        output = create_output_data(transcript_no_date_info, sample_initial_analysis_result)
        self.assertEqual(output["episode_date"], "2023-07-15") # From mocked datetime.now() via extract_date_from_title
        
        # 5. Handles ISO datetime string with time for release_date
        transcript_with_iso_datetime = {**sample_transcript_data, "release_date": "2024-03-10T10:00:00Z"}
        output = create_output_data(transcript_with_iso_datetime, sample_initial_analysis_result)
        self.assertEqual(output["episode_date"], "2024-03-10")

    def test_create_output_data_empty_analysis(self):
        empty_analysis = {"gegenwartsvorschlaege": []}
        output = create_output_data(sample_transcript_data, empty_analysis)
        self.assertIsNotNone(output)
        self.assertEqual(len(output["gegenwartsvorschlaege"]), 0)

    def test_create_output_data_none_analysis(self):
        output = create_output_data(sample_transcript_data, None)
        self.assertIsNone(output)
        
        output_malformed = create_output_data(sample_transcript_data, {"foo": "bar"}) # missing gegenwartsvorschlaege
        self.assertIsNone(output)

    def test_extract_date_from_title(self):
        self.assertEqual(extract_date_from_title("An Episode from 2023 about stuff"), "2023-01-01")
        self.assertEqual(extract_date_from_title("NoDateHere"), datetime.now().strftime("%Y-%m-%d"))
        with patch('gemini_analyzer.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2020, 5, 5)
            self.assertEqual(extract_date_from_title("NoDateHere either"), "2020-05-05")

    # --- Tests for analyze_transcript_with_gemini and proofread_analysis_with_gemini ---
    # We'll use a helper for these as their core logic is similar
    def _test_gemini_call_logic(self, function_to_test, model_name_in_call):
        mock_client = MagicMock(spec=genai.Client)
        mock_response = MagicMock()
        
        # Success Case
        expected_dict = {"result": "success"}
        mock_response.text = '```json\n' + json.dumps(expected_dict) + '\n```'
        mock_client.models.generate_content.return_value = mock_response
        
        result = function_to_test(mock_client, sample_transcript_data)
        self.assertEqual(result, expected_dict)
        mock_client.models.generate_content.assert_called_once()
        args, kwargs = mock_client.models.generate_content.call_args
        self.assertEqual(kwargs['model'], model_name_in_call)

        # JSON Extraction without markdown
        mock_client.reset_mock()
        mock_response.text = json.dumps(expected_dict)
        mock_client.models.generate_content.return_value = mock_response
        result = function_to_test(mock_client, sample_transcript_data)
        self.assertEqual(result, expected_dict)

        # JSON Decode Error
        mock_client.reset_mock()
        mock_response.text = '{"bad": "json"' # Malformed
        mock_client.models.generate_content.return_value = mock_response
        with patch('logging.warning') as mock_log:
            result = function_to_test(mock_client, sample_transcript_data)
            # proofread returns initial analysis on error, analyze returns None
            if "proofread" in function_to_test.__name__:
                 self.assertEqual(result, sample_transcript_data) # sample_transcript_data is used as initial_analysis here
            else:
                self.assertIsNone(result)
            mock_log.assert_any_call(unittest.mock.ANY, unittest.mock.ANY) # Check if logging.warning was called

        # Rate Limit/Retry
        mock_client.reset_mock()
        # Simulate ResourceExhausted which should trigger retry
        # For google.api_core.exceptions.ResourceExhausted, the message often contains "429" or "RESOURCE_EXHAUSTED"
        error_429 = types.generation_types.BlockedPromptException("Simulated 429 error") 
        # A more direct way to simulate the specific exception class if available,
        # or ensure the string check in the SUT handles this.
        # For this test, we rely on the string check in the SUT.
        # Let's make it an exception that contains "429" in its string representation.
        class MockResourceExhausted(Exception):
            def __init__(self, message):
                super().__init__(message)

        mock_client.models.generate_content.side_effect = [
            MockResourceExhausted("Error 429: Too many requests"), 
            mock_response # Success on second try
        ]
        mock_response.text = json.dumps(expected_dict) # Ensure success response is valid JSON
        
        with patch('time.sleep') as mock_sleep:
            result = function_to_test(mock_client, sample_transcript_data)
            self.assertEqual(result, expected_dict)
            self.assertEqual(mock_client.models.generate_content.call_count, 2)
            mock_sleep.assert_called_once()

        # API Error (Non-retryable)
        mock_client.reset_mock()
        mock_client.models.generate_content.side_effect = ValueError("Some other API error")
        with patch('logging.warning') as mock_log:
            result = function_to_test(mock_client, sample_transcript_data)
            if "proofread" in function_to_test.__name__:
                 self.assertEqual(result, sample_transcript_data)
            else:
                self.assertIsNone(result)
            mock_log.assert_any_call(unittest.mock.ANY, unittest.mock.ANY)
            self.assertEqual(mock_client.models.generate_content.call_count, 1) # No retry

    def test_analyze_transcript_with_gemini(self):
        # Note: For analyze_transcript_with_gemini, the second argument is transcript_data
        # We pass sample_transcript_data as the 'transcript_data' argument.
        self._test_gemini_call_logic(
            lambda client, data: analyze_transcript_with_gemini(client, data),
            "gemini-2.0-flash-thinking-exp-01-21" # Expected model for analyze
        )

    def test_proofread_analysis_with_gemini(self):
        # Note: For proofread_analysis_with_gemini, the second argument is initial_analysis
        # and the third is transcript_data. We'll use sample_initial_analysis_result for initial_analysis
        # and sample_transcript_data for transcript_data.
        # The lambda needs to be adjusted to reflect this.
        self._test_gemini_call_logic(
            lambda client, data: proofread_analysis_with_gemini(client, sample_initial_analysis_result, data),
            "gemini-2.0-pro-exp-02-05" # Expected model for proofread
        )

        # Test case where initial_analysis is None or malformed for proofread
        mock_client = MagicMock(spec=genai.Client)
        result_none = proofread_analysis_with_gemini(mock_client, None, sample_transcript_data)
        self.assertIsNone(result_none)
        
        result_malformed = proofread_analysis_with_gemini(mock_client, {"foo": "bar"}, sample_transcript_data)
        self.assertEqual(result_malformed, {"foo": "bar"})


if __name__ == '__main__':
    unittest.main()
