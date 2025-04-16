import pytest
import importlib

def test_import_gemini_analyzer():
    importlib.import_module('scripts.gemini_analyzer')

def test_main_runs(monkeypatch):
    import scripts.gemini_analyzer as ga
    # Patch setup_gemini_client to avoid real API calls
    monkeypatch.setattr(ga, 'setup_gemini_client', lambda: None)
    # Patch process_transcript to just return True
    monkeypatch.setattr(ga, 'process_transcript', lambda *a, **kw: True)
    # Patch argparse to avoid parsing real CLI args
    class DummyArgs:
        input_dir = 'data/transcripts'
        output_dir = 'data/analyses'
        file = None
    monkeypatch.setattr(ga, 'argparse', type('argparse', (), {'ArgumentParser': lambda *a, **kw: type('P', (), {'parse_args': lambda self=None: DummyArgs})}) )
    ga.main()
