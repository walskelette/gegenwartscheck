import unittest
from unittest.mock import patch, MagicMock, mock_open, call
import json
import os
import sys
import requests # Required for requests.exceptions.RequestException

# Add scripts directory to sys.path to allow importing spotify_fetch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

from spotify_fetch import (
    get_spotify_token,
    get_podcast_episodes,
    save_episodes,
    # main # Not explicitly testing main logic here, but could be if needed
)

# Sample Data for Tests
sample_spotify_episodes_page1 = {
    "items": [{"id": "ep1", "name": "Episode 1", "release_date": "2023-01-01", "external_urls": {"spotify": "url1"}, "description": "Desc 1", "duration_ms": 1000}],
    "next": "https://api.spotify.com/v1/shows/dummy_show_id/episodes?offset=1&limit=1",
    "total": 2,
    "limit": 1,
    "offset": 0
}

sample_spotify_episodes_page2 = {
    "items": [{"id": "ep2", "name": "Episode 2", "release_date": "2023-01-08", "external_urls": {"spotify": "url2"}, "description": "Desc 2", "duration_ms": 2000}],
    "next": None,
    "total": 2,
    "limit": 1,
    "offset": 1
}

class TestSpotifyFetchLogic(unittest.TestCase):

    # --- Tests for get_spotify_token ---
    @patch('requests.post')
    def test_get_spotify_token_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test_token", "expires_in": 3600}
        mock_response.raise_for_status = MagicMock() # Ensure it doesn't raise for success
        mock_post.return_value = mock_response

        token = get_spotify_token("test_client_id", "test_client_secret")

        self.assertEqual(token, "test_token")
        mock_post.assert_called_once_with(
            "https://accounts.spotify.com/api/token",
            headers={"Authorization": "Basic dGVzdF9jbGllbnRfaWQ6dGVzdF9jbGllbnRfc2VjcmV0"},
            data={"grant_type": "client_credentials"}
        )
        mock_response.raise_for_status.assert_called_once()

    @patch('requests.post')
    def test_get_spotify_token_api_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Error")
        mock_post.return_value = mock_response

        with self.assertRaises(requests.exceptions.HTTPError):
            get_spotify_token("test_client_id", "test_client_secret")
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


    @patch('requests.post', side_effect=requests.exceptions.RequestException("Network Error"))
    def test_get_spotify_token_request_exception(self, mock_post):
        with self.assertRaises(requests.exceptions.RequestException):
            get_spotify_token("test_client_id", "test_client_secret")
        mock_post.assert_called_once()

    # --- Tests for get_podcast_episodes ---
    @patch('requests.get')
    @patch('spotify_fetch.get_spotify_token', return_value="dummy_token")
    def test_get_podcast_episodes_single_page_success(self, mock_get_token, mock_get):
        mock_response = MagicMock()
        # Simulate a scenario where the first page is the only page
        single_page_data = {**sample_spotify_episodes_page1, "next": None}
        mock_response.json.return_value = single_page_data
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        episodes = get_podcast_episodes("test_client_id", "test_client_secret", "dummy_show_id")
        
        expected_episodes = [{
            "id": "ep1",
            "title": "Episode 1",
            "release_date": "2023-01-01",
            "url": "url1",
            "description": "Desc 1",
            "duration_ms": 1000
        }]
        self.assertEqual(episodes, expected_episodes)
        mock_get_token.assert_called_once_with("test_client_id", "test_client_secret")
        mock_get.assert_called_once_with(
            "https://api.spotify.com/v1/shows/dummy_show_id/episodes",
            headers={"Authorization": "Bearer dummy_token"},
            params={"limit": 50, "offset": 0, "market": "US"}
        )
        mock_response.raise_for_status.assert_called_once()

    @patch('requests.get')
    @patch('spotify_fetch.get_spotify_token', return_value="dummy_token")
    def test_get_podcast_episodes_multi_page_success(self, mock_get_token, mock_get):
        mock_response_page1 = MagicMock()
        mock_response_page1.json.return_value = sample_spotify_episodes_page1
        mock_response_page1.raise_for_status = MagicMock()

        mock_response_page2 = MagicMock()
        mock_response_page2.json.return_value = sample_spotify_episodes_page2
        mock_response_page2.raise_for_status = MagicMock()

        mock_get.side_effect = [mock_response_page1, mock_response_page2]

        episodes = get_podcast_episodes("test_client_id", "test_client_secret", "dummy_show_id")

        expected_episodes = [
            {"id": "ep1", "title": "Episode 1", "release_date": "2023-01-01", "url": "url1", "description": "Desc 1", "duration_ms": 1000},
            {"id": "ep2", "title": "Episode 2", "release_date": "2023-01-08", "url": "url2", "description": "Desc 2", "duration_ms": 2000}
        ]
        self.assertEqual(episodes, expected_episodes)
        mock_get_token.assert_called_once_with("test_client_id", "test_client_secret")
        
        calls = [
            call("https://api.spotify.com/v1/shows/dummy_show_id/episodes", headers={"Authorization": "Bearer dummy_token"}, params={"limit": 50, "offset": 0, "market": "US"}),
            call(sample_spotify_episodes_page1["next"], headers={"Authorization": "Bearer dummy_token"}) # Use the 'next' URL as-is without overriding its query parameters
        ]
        mock_get.assert_has_calls(calls)
        self.assertEqual(mock_get.call_count, 2)
        mock_response_page1.raise_for_status.assert_called_once()
        mock_response_page2.raise_for_status.assert_called_once()

    @patch('requests.get')
    @patch('spotify_fetch.get_spotify_token', return_value="dummy_token")
    def test_get_podcast_episodes_api_error(self, mock_get_token, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Error")
        mock_get.return_value = mock_response

        with self.assertRaises(requests.exceptions.HTTPError):
            get_podcast_episodes("test_client_id", "test_client_secret", "dummy_show_id")
        
        mock_get_token.assert_called_once()
        mock_get.assert_called_once() # Should fail on the first call
        mock_response.raise_for_status.assert_called_once()


    @patch('requests.get')
    @patch('spotify_fetch.get_spotify_token', return_value="dummy_token")
    def test_get_podcast_episodes_empty_response(self, mock_get_token, mock_get):
        mock_response = MagicMock()
        empty_data = {"items": [], "next": None, "total": 0, "limit": 50, "offset": 0}
        mock_response.json.return_value = empty_data
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        episodes = get_podcast_episodes("test_client_id", "test_client_secret", "dummy_show_id")

        self.assertEqual(episodes, [])
        mock_get_token.assert_called_once()
        mock_get.assert_called_once()


    # --- Tests for save_episodes ---
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_episodes_success(self, mock_json_dump, mock_file_open, mock_os_makedirs):
        sample_episodes_data = [
            {"id": "ep1", "title": "Episode 1"},
            {"id": "ep2", "title": "Episode 2"}
        ]
        output_filepath = "data/output/episodes.json"
        expected_dir = os.path.dirname(output_filepath)

        save_episodes(sample_episodes_data, output_filepath)

        mock_os_makedirs.assert_called_once_with(expected_dir, exist_ok=True)
        mock_file_open.assert_called_once_with(output_filepath, 'w', encoding='utf-8')
        mock_json_dump.assert_called_once_with(sample_episodes_data, mock_file_open(), indent=2, ensure_ascii=False)

    @patch('os.makedirs', side_effect=OSError("Failed to create directory"))
    def test_save_episodes_makedirs_os_error(self, mock_os_makedirs):
        sample_episodes_data = [{"id": "ep1"}]
        output_filepath = "data/output/episodes.json"
        
        with self.assertRaises(OSError): # Or check if logger.error was called if there's try-except in SUT
            save_episodes(sample_episodes_data, output_filepath)
        mock_os_makedirs.assert_called_once()

    @patch('os.makedirs') # Mock makedirs to prevent actual directory creation
    @patch('builtins.open', side_effect=IOError("Failed to open file"))
    def test_save_episodes_open_io_error(self, mock_file_open, mock_os_makedirs):
        sample_episodes_data = [{"id": "ep1"}]
        output_filepath = "data/output/episodes.json"
        
        with self.assertRaises(IOError): # Or check if logger.error was called
            save_episodes(sample_episodes_data, output_filepath)
        mock_os_makedirs.assert_called_once()
        mock_file_open.assert_called_once_with(output_filepath, 'w', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
