#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import json
import os
import glob
import re
import argparse
import time
import random
import logging
from datetime import datetime
from pathlib import Path
from google import genai
from google.genai import types
from typing import Any, Dict, Optional

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Konstanten für die Verarbeitung
DATA_DIR = "data/transcripts"
OUTPUT_DIR = "data/analyses"
MODEL_NAME = "gemini-2.0-flash-thinking-exp-01-21"
PROOFREADING_MODEL_NAME = "gemini-2.0-pro-exp-02-05"

def setup_gemini_client() -> genai.Client:
    """Initialisiert den Gemini API-Client mit dem API-Schlüssel aus der Umgebungsvariable."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY Umgebungsvariable ist nicht gesetzt")
    
    client = genai.Client(api_key=api_key)
    return client

def load_transcript(file_path: str) -> dict:
    """Lädt eine Transkript-Datei und gibt deren Inhalt zurück."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_gemini_prompt(transcript_data: dict) -> str:
    """Erstellt einen Prompt für die Gemini API, der aus dem Transkript die relevanten Informationen extrahiert."""
    # Extract speakers
    speakers = {}
    for item in transcript_data["transcript"]:
        speaker = item["speaker"]
        if speaker not in speakers and speaker.startswith("SPEAKER_"):
            speakers[speaker] = speaker

    transcript_text = ""
    for item in transcript_data["transcript"]:
        speaker = item["speaker"]
        text = item["text"]
        transcript_text += f"{speaker}: {text}\n\n"

    episode_title = transcript_data.get("episode_title", "Unbekannte Episode")
    
    prompt = f"""Du bist ein persönlicher Assistent, der dabei hilft, Vorschläge zu identifizieren, die in dem Podcast "Gegenwart" gemacht werden.

In diesem Podcast schlagen die Hosts gegenwärtige Phänomene vor, und der andere Host entscheidet, ob ein Punkt dafür vergeben wird oder nicht. Ein Punkt wird vergeben, wenn der Vorschlag tatsächlich ein Phänomen der Gegenwart beschreibt, das neu und relevant ist.

Die Hosts sind Lars Weisbrod und Ijoma Mangold. Manchmal ist statt Ijoma auch Nina Pauer dabei.

Hier ist der Transkript-Text einer Podcast-Episode mit dem Titel "{episode_title}":

{transcript_text}

Identifiziere alle "Gegenwartsvorschläge" in diesem Transkript und extrahiere die folgenden Informationen für jeden Vorschlag:

1. vorschlag: Der Name des Gegenwartsvorschlags
2. vorschlagender: Wer hat den Vorschlag gemacht? (Nur Lars, Ijoma oder Nina)
3. ist_hoerer: War es ein Vorschlag von einem Hörer oder einer Hörerin? (true/false)
4. hoerer_name: Name des Hörers oder der Hörerin, falls vorhanden
5. begruendung: Die Begründung für den Vorschlag 
6. metaebene: Metaebene des Vorschlags, falls diskutiert
7. punkt_erhalten: Hat der Vorschlag einen Punkt bekommen? (true/false)
8. punkt_von: Wer hat den Punkt vergeben? (Lars, Ijoma oder Nina) - muss immer angegeben werden, null wenn kein Punkt vergeben wurde
9. tags: 5 Keywords oder Tags, die das Thema des Vorschlags beschreiben
10. start_zeit: Ab welcher Sekunde beginnt die Diskussion des Vorschlags? Gib nur die Zahl ohne "s" an (z.B. "120" statt "120s")

Formatiere deine Antwort als JSON mit folgendem Schema:
{{
  "gegenwartsvorschlaege": [
    {{
      "vorschlag": "Name des Vorschlags",
      "vorschlagender": "Lars/Ijoma/Nina",
      "ist_hoerer": true/false,
      "hoerer_name": "Name oder null",
      "begruendung": "Begründung für den Vorschlag",
      "metaebene": "Metaebene (falls explizit erwähnt, sonst null)",
      "punkt_erhalten": true/false,
      "punkt_von": "Lars/Ijoma/Nina",
      "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
      "start_zeit": "123"
    }}
  ]
}}

WICHTIG:
- "start_zeit" ist eine Zeichenkette, die NUR die Zahl der Sekunden ohne das "s" am Ende enthält
- "punkt_von" muss IMMER angegeben werden (auch, wenn kein Punkt vergeben wurde)
- "vorschlagender" muss IMMER einer der Hosts sein (Lars, Ijoma oder Nina)
- Stelle sicher, dass das JSON-Format korrekt ist.
"""

    return prompt

def analyze_transcript_with_gemini(client: genai.Client, transcript_data: dict) -> Optional[dict]:
    """Analysiert ein Transkript mit der Gemini API."""
    prompt_text = create_gemini_prompt(transcript_data)
    
    # Create content structure for the prompt
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_text)]
        )
    ]
    
    # Add Google Grounding tool
    tools = [types.Tool(google_search=types.GoogleSearch())]
    
    # Create generation config
    generate_content_config = types.GenerateContentConfig(
        temperature=0.1,
        top_p=0.9,
        top_k=40,
        max_output_tokens=4096,
        tools=tools,
        response_mime_type="text/plain",
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            )
        ]
    )
    
    # Retry mechanism with respect to 2 rpm rate limit
    max_retries = 5
    min_retry_delay = 30  # seconds (30s = respecting 2 rpm)
    
    for retry_attempt in range(max_retries):
        try:
            # Generate content using the model
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=generate_content_config
            )
            
            response_text = response.text
            
            # JSON aus der Antwort extrahieren
            # Oft gibt Gemini das JSON in einem Markdown-Codeblock zurück
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Falls kein Markdown-Block gefunden wurde, versuchen wir, die gesamte Antwort zu parsen
                json_text = response_text
            
            try:
                result = json.loads(json_text)
                return result
            except json.JSONDecodeError as e:
                logging.warning(f"Fehler beim Parsen der Gemini-Antwort: {e}")
                logging.warning(f"Antworttext: {response_text}")
                return None
                
        except Exception as e:
            # Check if it's a rate limit error
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if retry_attempt < max_retries - 1:  # Don't sleep on the last attempt
                    # Use a fixed delay based on rate limit of 2 rpm
                    delay = min_retry_delay + (retry_attempt * 5) + random.uniform(0, 2)
                    logging.warning(f"Rate limit erreicht (max 2 rpm). Warte {delay:.2f} Sekunden vor Versuch {retry_attempt + 2}/{max_retries}...")
                    time.sleep(delay)
                else:
                    logging.warning(f"Maximale Anzahl von Versuchen erreicht. Fehler: {e}")
            else:
                # If it's not a rate limit error, don't retry
                logging.warning(f"Fehler bei der Gemini API-Anfrage: {e}")
                break
    
    # If all retries failed
    return None

def proofread_analysis_with_gemini(client: genai.Client, initial_analysis: dict, transcript_data: dict) -> dict:
    """Führt eine zweite Analyse zur Verbesserung und Korrektur der ersten Analyse durch."""
    if not initial_analysis or "gegenwartsvorschlaege" not in initial_analysis:
        logging.info("Keine Analyse zum Korrekturlesen vorhanden.")
        return initial_analysis
    
    # Erstellen eines strukturierten JSON-Strings für den Prompt
    initial_json_str = json.dumps(initial_analysis, indent=2, ensure_ascii=False)
    
    # Extrahieren des Podcast-Titels für den Kontext
    podcast_title = transcript_data.get("episode_title", "Unbekannter Podcast")
    
    # Erstellen des Proofreading-Prompts
    prompt_text = f"""
Du bist ein Korrektur-Assistent für Podcast-Analysen des deutschen Podcasts "Die sogenannte Gegenwart". Du erhältst eine automatisch erstellte Analyse 
der Folge mit dem Titel "{podcast_title}".

# Wichtige Kontextinformationen
Die Analyse basiert auf einem automatisch generierten Transkript eines deutschsprachigen Podcasts. Bei der Spracherkennung und Transkription treten häufig Fehler auf, besonders bei:
- Fremdwörtern und Lehnwörtern aus anderen Sprachen (Englisch, Französisch, etc.)
- Neologismen und neu erfundenen Begriffen
- Markennamen und Produktbezeichnungen
- Internet-Trends und Social-Media-Begriffen
- Fachbegriffen aus verschiedenen Domänen

Diese Wörter sind besonders anfällig für Transkriptionsfehler, da sie oft falsch erkannt oder verstanden werden.

# Aufgabe
Deine Aufgabe ist AUSSCHLIESSLICH die Überprüfung der Rechtschreibung von Konzepten, Marken und Fachbegriffen:

1. Überprüfe für jeden extrahierten "vorschlag" und jedes wichtige Konzept in der "begruendung", ob die Schreibweise korrekt ist.
2. Nutze IMMER das Google-Grounding-Tool, um die korrekte Schreibweise zu verifizieren.
3. Korrigiere falsch geschriebene Konzepte, Marken, Namen und Fachbegriffe, die wegen Transkriptionsfehlern falsch geschrieben sein könnten.
4. Du MUSST für jeden "vorschlag" das Google-Grounding-Tool verwenden, um die Schreibweise zu überprüfen.

# Wichtige Einschränkungen
1. Ändere KEINE inhaltlichen Aspekte der Analyse.
2. Verändere NICHT die grundlegende Struktur oder Bedeutung der Daten.
3. Füge KEINE neuen Tags hinzu und ändere die Tags nur, wenn sie falsch geschrieben sind.
4. Erweitere NICHT die "begruendung" oder andere Textfelder inhaltlich.
5. Übersetze KEINE Inhalte in eine andere Sprache - alle Texte bleiben in ihrer Originalsprache.
6. Konzentriere dich NUR auf mögliche Fehler, die durch Spracherkennung oder Transkription entstanden sein könnten.

Hier ist die zu korrigierende Analyse im JSON-Format:

```json
{initial_json_str}
```

Antworte nur mit dem verbesserten JSON-Format. Füge keine Erklärungen oder zusätzlichen Text hinzu.
"""
    
    # Create content structure for the prompt
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_text)]
        )
    ]
    
    # Add Google Grounding tool
    tools = [types.Tool(google_search=types.GoogleSearch())]
    
    # Create generation config
    generate_content_config = types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        top_k=40,
        max_output_tokens=4096,
        tools=tools,
        response_mime_type="text/plain",
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            )
        ]
    )
    
    # Retry mechanism with respect to 2 rpm rate limit
    max_retries = 5
    min_retry_delay = 30  # seconds (30s = respecting 2 rpm)
    
    for retry_attempt in range(max_retries):
        try:
            # Generate content using the model
            response = client.models.generate_content(
                model=PROOFREADING_MODEL_NAME,
                contents=contents,
                config=generate_content_config
            )
            
            response_text = response.text
            
            # JSON aus der Antwort extrahieren
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Falls kein Markdown-Block gefunden wurde, versuchen wir, die gesamte Antwort zu parsen
                json_text = response_text
            
            try:
                result = json.loads(json_text)
                logging.info("Zweite Analyse (Korrekturlesen) erfolgreich durchgeführt.")
                return result
            except json.JSONDecodeError as e:
                logging.warning(f"Fehler beim Parsen der Proofreading-Antwort: {e}")
                logging.warning(f"Antworttext: {response_text}")
                return initial_analysis  # Rückgabe der ursprünglichen Analyse bei Fehler
                
        except Exception as e:
            # Check if it's a rate limit error
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if retry_attempt < max_retries - 1:  # Don't sleep on the last attempt
                    # Use a fixed delay based on rate limit of 2 rpm
                    delay = min_retry_delay + (retry_attempt * 5) + random.uniform(0, 2)
                    logging.warning(f"Rate limit erreicht (max 2 rpm). Warte {delay:.2f} Sekunden vor Versuch {retry_attempt + 2}/{max_retries}...")
                    time.sleep(delay)
                else:
                    logging.warning(f"Maximale Anzahl von Versuchen erreicht. Fehler: {e}")
            else:
                # If it's not a rate limit error, don't retry
                logging.warning(f"Fehler bei der Proofreading-API-Anfrage: {e}")
                break
    
    # If all retries failed, return the initial analysis
    return initial_analysis

def extract_date_from_title(title: str) -> str:
    """Versucht, ein Datum aus dem Episodentitel zu extrahieren."""
    # Einfache Methode: Suche nach einem vierstelligen Jahr
    year_match = re.search(r'20\d{2}', title)
    if year_match:
        return f"{year_match.group(0)}-01-01"  # Standarddatum, wenn nur Jahr bekannt
    
    # Falls kein Datum gefunden wurde, verwenden wir das aktuelle Datum
    return datetime.now().strftime("%Y-%m-%d")

def create_output_data(transcript_data: dict, analysis_result: dict) -> Optional[dict]:
    """Erstellt die finalen Ausgabedaten aus den Transkript- und Analysedaten."""
    if not analysis_result or "gegenwartsvorschlaege" not in analysis_result:
        return None
    
    # Use release_date if available, otherwise fall back to extracted date or title-based date
    episode_date = transcript_data.get("release_date", transcript_data.get("upload_date"))
    if not episode_date:
        # For backward compatibility
        episode_date = extract_date_from_title(transcript_data.get("episode_title", ""))
    
    # If episode_date is an ISO format string with time, extract just the date portion
    if isinstance(episode_date, str) and "T" in episode_date:
        episode_date = episode_date.split("T")[0]
    
    # Get apple_id and spotify_id from transcript_data
    apple_id = transcript_data.get("apple_id", "")
    spotify_id = transcript_data.get("spotify_id", "")
    
    # If only one ID is available, use that for both fields
    if not apple_id and spotify_id:
        apple_id = spotify_id
    elif not spotify_id and apple_id:
        spotify_id = apple_id
    
    # Process gegenwartsvorschlaege to ensure required fields exist and format is correct
    vorschlaege = analysis_result["gegenwartsvorschlaege"]
    for vorschlag in vorschlaege:
        # Ensure punkt_von is always included
        if "punkt_von" not in vorschlag:
            vorschlag["punkt_von"] = None
            
        # Ensure punkt_erhalten is always included
        if "punkt_erhalten" not in vorschlag:
            vorschlag["punkt_erhalten"] = False
            
        # Ensure start_zeit is included without "s" suffix
        if "start_zeit" not in vorschlag:
            vorschlag["start_zeit"] = None
        elif isinstance(vorschlag["start_zeit"], str) and vorschlag["start_zeit"].endswith("s"):
            vorschlag["start_zeit"] = vorschlag["start_zeit"][:-1]
            
        # Remove ende_zeit field if it exists
        if "ende_zeit" in vorschlag:
            del vorschlag["ende_zeit"]
            
        # Ensure vorschlagender is one of the hosts
        if "vorschlagender" not in vorschlag or vorschlag["vorschlagender"] not in ["Lars", "Ijoma", "Nina"]:
            # If a listener was the source, set vorschlagender to the host who presented it
            if vorschlag.get("ist_hoerer", False) and "hoerer_name" in vorschlag and vorschlag["hoerer_name"]:
                # Default to Lars if we can't determine who presented it
                vorschlag["vorschlagender"] = "Lars"
    
    return {
        "episode_title": transcript_data.get("episode_title", "Unbekannte Episode"),
        "apple_id": apple_id,
        "spotify_id": spotify_id,
        "episode_date": episode_date,
        "gegenwartsvorschlaege": vorschlaege
    }

def validate_output_schema(output_data: dict) -> bool:
    """Validiert das Ausgabeschema grob, um offensichtliche Fehler zu vermeiden."""
    required_fields = ["episode_title", "apple_id", "spotify_id", "episode_date", "gegenwartsvorschlaege"]
    for field in required_fields:
        if field not in output_data:
            logging.warning(f"Fehlendes Feld im Output: {field}")
            return False
    if not isinstance(output_data["gegenwartsvorschlaege"], list):
        logging.warning("'gegenwartsvorschlaege' ist nicht vom Typ Liste.")
        return False
    return True

def save_output_data(output_data: dict, output_path: str) -> None:
    """Speichert die Ausgabedaten als JSON-Datei."""
    if not validate_output_schema(output_data):
        logging.warning(f"Ungültiges Ausgabeschema, Datei wird nicht gespeichert: {output_path}")
        return
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        logging.info(f"Ausgabedaten gespeichert in: {output_path}")
    except Exception as e:
        logging.error(f"Fehler beim Speichern der Ausgabedaten in {output_path}: {e}")

def get_output_filename(input_filename: str) -> str:
    """Erzeugt einen Ausgabedateinamen basierend auf dem Eingabedateinamen."""
    base_name = os.path.basename(input_filename)
    # Extrahiere die ID aus dem Dateinamen (Teil vor "_transcript.json")
    id_match = re.match(r'(.*)_transcript\.json', base_name)
    if id_match:
        primary_id = id_match.group(1)
        return f"{primary_id}.json"
    else:
        # Fallback, falls das Muster nicht passt (sollte nicht vorkommen bei korrekten Eingabedateien)
        return base_name.replace("_transcript.json", "_gegenwartscheck.json")

def get_existing_analysis(output_path: str) -> Optional[dict]:
    """Lädt bestehende Analysedaten, falls vorhanden und gültig."""
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                if existing_data.get("gegenwartsvorschlaege"):
                    return existing_data
        except Exception as e:
            logging.warning(f"Fehler beim Laden bestehender Analysedatei {output_path}: {e}")
    return None

def process_transcript(client: genai.Client, file_path: str, output_dir: str) -> bool:
    """Verarbeitet eine einzelne Transkript-Datei und speichert die Analyse, falls noch nicht vorhanden."""
    try:
        logging.info(f"Verarbeite Transkript: {file_path}")
        transcript_data = load_transcript(file_path)
        output_filename = get_output_filename(file_path)
        output_path = os.path.join(output_dir, output_filename)
        existing_data = get_existing_analysis(output_path)
        if existing_data:
            logging.info(f"Überspringe Verarbeitung, da bereits analysiert: {file_path}")
            return True
        
        # Transcript analysieren
        logging.info("Führe erste Analyse durch...")
        initial_analysis = analyze_transcript_with_gemini(client, transcript_data)
        
        if not initial_analysis or "gegenwartsvorschlaege" not in initial_analysis or not initial_analysis["gegenwartsvorschlaege"]:
            logging.info(f"Keine Gegenwartsvorschläge gefunden in: {file_path}")
            # Leeres Ergebnis speichern, um in Zukunft zu überspringen
            empty_result = {"gegenwartsvorschlaege": []}
            output_data = create_output_data(transcript_data, empty_result)
            save_output_data(output_data, output_path)
            return True
        
        logging.info(f"Gefundene Vorschläge: {len(initial_analysis['gegenwartsvorschlaege'])}")
        
        # Zweite Analyse durchführen (Korrektur und Verbesserung)
        logging.info("Führe zweite Analyse zur Verbesserung durch...")
        final_analysis = proofread_analysis_with_gemini(client, initial_analysis, transcript_data)
        
        # Ausgabedaten erstellen
        output_data = create_output_data(transcript_data, final_analysis)
        
        if not output_data:
            logging.warning(f"Warnung: Keine gültigen Ausgabedaten für {file_path}")
            return False
        
        # Ausgabedatei speichern
        output_path = os.path.join(output_dir, output_filename)
        save_output_data(output_data, output_path)
        
        return True
        
    except Exception as e:
        logging.warning(f"Fehler bei der Verarbeitung von {file_path}: {e}")
        return False

def main() -> None:
    """Hauptfunktion zum Ausführen des Skripts."""
    
    parser = argparse.ArgumentParser(description="Analysiert Podcast-Transkripte mit der Gemini API")
    parser.add_argument("--input-dir", default=DATA_DIR, help="Verzeichnis mit den Transkript-Dateien")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Verzeichnis für die Ausgabedaten")
    parser.add_argument("--file", help="Spezifische Datei zum Verarbeiten (optional)")
    args = parser.parse_args()
    
    # Gemini-Client initialisieren
    client = setup_gemini_client()
    
    # Ausgabeverzeichnis erstellen, falls es nicht existiert
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Transkript-Dateien finden
    if args.file:
        transcript_files = [args.file]
    else:
        transcript_files = glob.glob(os.path.join(args.input_dir, "*_transcript.json"))
    
    logging.info(f"Gefundene Transkript-Dateien: {len(transcript_files)}")
    
    # Transkripte verarbeiten
    success_count = 0
    for file_path in transcript_files:
        if process_transcript(client, file_path, args.output_dir):
            success_count += 1
    
    logging.info(f"Verarbeitung abgeschlossen. {success_count} von {len(transcript_files)} Transkripten erfolgreich verarbeitet.")

if __name__ == "__main__":
    main()