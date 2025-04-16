import pytest
import importlib

def test_import_spotify_fetch():
    importlib.import_module('scripts.spotify_fetch')

def test_main_runs(monkeypatch):
    import scripts.spotify_fetch as sf
    # Patch get_podcast_episodes to avoid real API calls
    monkeypatch.setattr(sf, 'get_podcast_episodes', lambda *a, **kw: [])
    # Patch os.environ to provide dummy credentials
    monkeypatch.setitem(sf.os.environ, 'SPOTIFY_CLIENT_ID', 'dummy')
    monkeypatch.setitem(sf.os.environ, 'SPOTIFY_CLIENT_SECRET', 'dummy')
    monkeypatch.setitem(sf.os.environ, 'SPOTIFY_SHOW_ID', 'dummy')
    sf.main()
