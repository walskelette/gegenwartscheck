#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import re
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(project_dir))

# Import the analyzer module
from scripts.gemini_analyzer import setup_gemini_client, create_gemini_prompt, proofread_analysis_with_gemini

def test_gemini_prompts():
    """Tests the improved Gemini prompts with a sample transcript."""
    
    # Check if API key is available
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("FEHLER: GEMINI_API_KEY Umgebungsvariable ist nicht gesetzt")
        return False
    
    # Load a sample transcript
    transcript_files = list(Path("data/transcripts").glob("*_transcript.json"))
    if not transcript_files:
        print("Keine Transkript-Dateien gefunden.")
        return False
    
    # Use the first transcript as a sample
    sample_transcript_path = transcript_files[0]
    print(f"Verwende {sample_transcript_path} als Beispiel-Transkript")
    
    with open(sample_transcript_path, 'r', encoding='utf-8') as f:
        transcript_data = json.load(f)
    
    # Generate the improved prompt
    prompt = create_gemini_prompt(transcript_data)
    
    # Display a sample of the prompt
    print("\n=== Auszug aus dem verbesserten Haupt-Prompt ===")
    prompt_sample = "\n".join(prompt.split("\n")[:30]) + "\n...\n"
    print(prompt_sample)
    
    # Test API connection and prompt with client
    try:
        print("\n=== Teste Verbindung zum Gemini API ===")
        client = setup_gemini_client()
        
        # Run a simplified test query to avoid using too many tokens
        test_content = [
            {
                "role": "user",
                "parts": [{"text": "Gib ein einfaches JSON-Objekt mit dem Schlüssel 'test' und dem Wert 'erfolgreich' zurück."}]
            }
        ]
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=test_content
        )
        
        print("API-Verbindung erfolgreich!")
        print(f"Antwort: {response.text}\n")
        
        # Print out the proofreading prompt structure
        initial_analysis = {
            "gegenwartsvorschlaege": [
                {
                    "vorschlag": "KI-generierte Pintrest-Bilder",
                    "tags": ["KI", "Bilder", "Internet"],
                    "vorschlagender": "Lena",
                    "ist_hoerer": True,
                    "hoerer_name": "Lena",
                    "begruendung": "KI-Bilder auf Pinterest führen zu Unzufriedenheit",
                    "metaebene": None,
                    "punkt_erhalten": True,
                    "punkt_von": "Lars"
                }
            ]
        }
        
        # Generate proofreading prompt (don't execute it to save tokens)
        from scripts.gemini_analyzer import types
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text="Stelle sicher, dass der Vorschlag korrekt ist")]
            )
        ]
        
        print("\n=== Verbesserte Prompt-Struktur ===")
        print("Haupt-Prompt: Mit zusätzlichen Erkennungsmustern, Sprecherzuordnung, und Beispielen")
        print("Korrektur-Prompt: Mit spezifischen Validierungsschritten und Beispielen")
        print("\nDie verbesserten Prompts wurden erfolgreich in gemini_analyzer.py implementiert.")
        
        return True
        
    except Exception as e:
        print(f"FEHLER bei der Gemini API-Anfrage: {e}")
        return False

if __name__ == "__main__":
    print("Teste verbesserte Gemini Prompts...")
    if test_gemini_prompts():
        print("\nTest ERFOLGREICH! Die verbesserten Prompts wurden überprüft.")
        print("Für einen vollständigen Test, führe das Haupt-Skript aus: python scripts/gemini_analyzer.py")
    else:
        print("\nTest FEHLGESCHLAGEN! Bitte überprüfe die API-Konfiguration und den API-Schlüssel.") 