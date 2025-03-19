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
from datetime import datetime
from pathlib import Path
from google import genai
from google.genai import types

# Konstanten für die Verarbeitung
DATA_DIR = "data/transcripts"
OUTPUT_DIR = "data/analyses"
MODEL_NAME = "gemini-2.0-flash-thinking-exp-01-21"
PROOFREADING_MODEL_NAME = "gemini-2.0-flash"

def setup_gemini_client():
    """Initialisiert den Gemini API-Client mit dem API-Schlüssel aus der Umgebungsvariable."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY Umgebungsvariable ist nicht gesetzt")
    
    client = genai.Client(api_key=api_key)
    return client

def load_transcript(file_path):
    """Lädt eine Transkript-Datei und gibt deren Inhalt zurück."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_gemini_prompt(transcript_data):
    """Erstellt einen detaillierten Prompt für die Gemini API zur Analyse des Transkripts."""
    
    # Transkript-Text für den Prompt vorbereiten
    transcript_text = ""
    for item in transcript_data["transcript"]:
        speaker = item["speaker"]
        text = item["text"]
        
        # Include timestamp information if available
        time_info = ""
        if "begin_time" in item and "duration_seconds" in item:
            time_info = f"[Zeit: {item['begin_time']}, Dauer: {round(item['duration_seconds'], 2)}s] "
        elif "begin_seconds" in item:
            time_info = f"[Zeit: {round(item['begin_seconds'], 2)}s] "
            
        transcript_text += f"{speaker}: {time_info}{text}\n\n"
    
    prompt = f"""
Du bist ein Analyse-Assistent, der dabei hilft, bestimmte Segmente aus Podcast-Transkripten des Podcasts "Die sogenannte Gegenwart" zu extrahieren und zu strukturieren.

# Hintergrund zum Podcast
"Die sogenannte Gegenwart" ist ein deutscher Podcast mit Nina Pauer, Lars Weisbrod und Ijoma Mangold. In fast jeder Folge spielen die Hosts ein Spiel namens "Gegenwartscheck".

# Regeln des Gegenwartscheck
- Die Teilnehmer schlagen Konzepte, Ideen, Beobachtungen oder Trends vor, die sie für "gegenwärtig" halten
- Jeder Vorschlag wird begründet und diskutiert
- Am Ende entscheidet einer der anderen Teilnehmer, ob der Vorschlag einen "Punkt" bekommt oder nicht
- Manchmal werden auch Vorschläge von Hörern diskutiert

# Erkennungsmuster für Gegenwartsvorschläge
Gegenwartsvorschläge werden oft mit bestimmten Phrasen eingeleitet:
- "Ich habe als Gegenwartscheck (mitgebracht)..."
- "Mein Gegenwartscheck ist/wäre..."
- "Ich hätte als Gegenwartscheck..."
- "Für den Gegenwartscheck schlage ich vor..."
- "Ich habe für den Gegenwartscheck..."
- "Als Gegenwartscheck würde ich vorschlagen..."

# Zuordnung der Sprecher zu Podcast-Hosts
Im Transkript werden die Sprecher als SPEAKER_X bezeichnet. 
- Versuche, die Sprecher anhand des Kontexts und der Namen in den Gesprächen zuzuordnen
- Beachte, dass meist Nina Pauer, Lars Weisbrod und Ijoma Mangold an den Gesprächen teilnehmen
- Wenn Hörer-Vorschläge diskutiert werden, wird der Name oft im Kontext genannt

# Detaillierte Feldbeschreibungen
- vorschlag: Der Kern-Begriff oder die Idee, die als gegenwärtig vorgeschlagen wird. Nur der Name ohne weitere Erklärungen.
- begruendung: Die vollständige Erläuterung, warum der Vorschlag gegenwärtig ist.
- metaebene: Ein weiterer Kontext oder eine übergeordnete Bedeutung, die explizit erwähnt wird. Nur ausfüllen, wenn klar als Metaebene benannt.
- tags: 3-5 präzise Schlagwörter, die den thematischen Bereich des Vorschlags erfassen.

# Umgang mit unvollständigen Informationen
- Wenn das Transkript unvollständig ist oder Informationen fehlen, verwende null als Wert.
- Spekuliere nicht über fehlende Informationen, sondern dokumentiere nur, was klar im Transkript erkennbar ist.
- Bei unklaren Punktvergaben: Setze punkt_erhalten = false und punkt_von = null.

# Deine Aufgabe
Analysiere das folgende Transkript und extrahiere alle "Gegenwartscheck"-Vorschläge mit folgenden Informationen:
1. Wer den Vorschlag gemacht hat (Nina, Lars, Ijoma oder ein Hörer)
2. Falls es ein Hörer-Vorschlag ist, den Namen des Hörers
3. Den vorgeschlagenen Begriff/Konzept/Trend
4. Die Begründung für den Vorschlag
5. Eine eventuell erwähnte "Metaebene"
6. Ob der Vorschlag einen Punkt erhalten hat und von wem
7. Erstelle für jeden Vorschlag 3-5 passende thematische Tags
8. Die Zeitstempel, wann der Vorschlag beginnt und endet (falls im Transkript vorhanden)

# Ausgabeformat
Antworte ausschließlich im folgenden JSON-Format:

```json
{{
  "gegenwartsvorschlaege": [
    {{
      "vorschlag": "Name des Gegenwartsvorschlags",
      "vorschlagender": "Nina/Lars/Ijoma/[Name des Hörers]",
      "ist_hoerer": true/false,
      "hoerer_name": "Name des Hörers (falls vorhanden, sonst null)",
      "begruendung": "Begründung für den Vorschlag",
      "metaebene": "Metaebene (falls explizit erwähnt, sonst null)",
      "punkt_erhalten": true/false,
      "punkt_von": "Nina/Lars/Ijoma (falls Punkt erhalten, sonst null)",
      "tags": ["Tag1", "Tag2", "Tag3"],
      "start_zeit": "Startzeit in Sekunden oder Zeitformat (falls vorhanden, sonst null)",
      "ende_zeit": "Endzeit in Sekunden oder Zeitformat (falls vorhanden, sonst null)"
    }}
  ]
}}
```

# Transkript für die Analyse
Podcast-Titel: {transcript_data["episode_title"]}
Podcast-ID: {transcript_data["podcast_id"]}
Extrahiert am: {transcript_data["extracted_date"]}

{transcript_text}

Antworte ausschließlich mit dem JSON-Format. Füge keine Erklärungen oder zusätzlichen Text hinzu.
"""
    
    return prompt

def analyze_transcript_with_gemini(client, transcript_data):
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
                print(f"Fehler beim Parsen der Gemini-Antwort: {e}")
                print(f"Antworttext: {response_text}")
                return None
                
        except Exception as e:
            # Check if it's a rate limit error
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if retry_attempt < max_retries - 1:  # Don't sleep on the last attempt
                    # Use a fixed delay based on rate limit of 2 rpm
                    delay = min_retry_delay + (retry_attempt * 5) + random.uniform(0, 2)
                    print(f"Rate limit erreicht (max 2 rpm). Warte {delay:.2f} Sekunden vor Versuch {retry_attempt + 2}/{max_retries}...")
                    time.sleep(delay)
                else:
                    print(f"Maximale Anzahl von Versuchen erreicht. Fehler: {e}")
            else:
                # If it's not a rate limit error, don't retry
                print(f"Fehler bei der Gemini API-Anfrage: {e}")
                break
    
    # If all retries failed
    return None

def proofread_analysis_with_gemini(client, initial_analysis, transcript_data):
    """Führt eine zweite Analyse zur Verbesserung und Korrektur der ersten Analyse durch."""
    if not initial_analysis or "gegenwartsvorschlaege" not in initial_analysis:
        print("Keine Analyse zum Korrekturlesen vorhanden.")
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
                print("Zweite Analyse (Korrekturlesen) erfolgreich durchgeführt.")
                return result
            except json.JSONDecodeError as e:
                print(f"Fehler beim Parsen der Proofreading-Antwort: {e}")
                print(f"Antworttext: {response_text}")
                return initial_analysis  # Rückgabe der ursprünglichen Analyse bei Fehler
                
        except Exception as e:
            # Check if it's a rate limit error
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if retry_attempt < max_retries - 1:  # Don't sleep on the last attempt
                    # Use a fixed delay based on rate limit of 2 rpm
                    delay = min_retry_delay + (retry_attempt * 5) + random.uniform(0, 2)
                    print(f"Rate limit erreicht (max 2 rpm). Warte {delay:.2f} Sekunden vor Versuch {retry_attempt + 2}/{max_retries}...")
                    time.sleep(delay)
                else:
                    print(f"Maximale Anzahl von Versuchen erreicht. Fehler: {e}")
            else:
                # If it's not a rate limit error, don't retry
                print(f"Fehler bei der Proofreading-API-Anfrage: {e}")
                break
    
    # If all retries failed, return the initial analysis
    return initial_analysis

def extract_date_from_title(title):
    """Versucht, ein Datum aus dem Episodentitel zu extrahieren."""
    # Einfache Methode: Suche nach einem vierstelligen Jahr
    year_match = re.search(r'20\d{2}', title)
    if year_match:
        return f"{year_match.group(0)}-01-01"  # Standarddatum, wenn nur Jahr bekannt
    
    # Falls kein Datum gefunden wurde, verwenden wir das aktuelle Datum
    return datetime.now().strftime("%Y-%m-%d")

def create_output_data(transcript_data, analysis_result):
    """Erstellt die finalen Ausgabedaten aus den Transkript- und Analysedaten."""
    if not analysis_result or "gegenwartsvorschlaege" not in analysis_result:
        return None
    
    # Use release_date if available, otherwise fall back to extracted date or title-based date
    episode_date = transcript_data.get("release_date")
    if not episode_date:
        # For backward compatibility
        episode_date = extract_date_from_title(transcript_data["episode_title"])
    
    # If episode_date is an ISO format string with time, extract just the date portion
    if isinstance(episode_date, str) and "T" in episode_date:
        episode_date = episode_date.split("T")[0]
    
    # Process gegenwartsvorschlaege to ensure timestamp information is preserved
    vorschlaege = analysis_result["gegenwartsvorschlaege"]
    for vorschlag in vorschlaege:
        # Ensure start_zeit and ende_zeit fields exist
        if "start_zeit" not in vorschlag:
            vorschlag["start_zeit"] = None
        if "ende_zeit" not in vorschlag:
            vorschlag["ende_zeit"] = None
    
    return {
        "episode_title": transcript_data["episode_title"],
        "podcast_id": transcript_data["podcast_id"],
        "episode_id": transcript_data.get("episode_id"),
        "episode_date": episode_date,
        "extracted_date": datetime.now().isoformat(),
        "gegenwartsvorschlaege": vorschlaege
    }

def save_output_data(output_data, output_path):
    """Speichert die Ausgabedaten als JSON-Datei."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"Ausgabedaten gespeichert in: {output_path}")

def get_output_filename(input_filename):
    """Erzeugt einen Ausgabedateinamen basierend auf dem Eingabedateinamen."""
    base_name = os.path.basename(input_filename)
    # Entferne "_transcript" und ändere die Erweiterung zu "_gegenwartscheck.json"
    output_name = base_name.replace("_transcript.json", "_gegenwartscheck.json")
    return output_name

def process_transcript(client, file_path, output_dir):
    """Verarbeitet eine einzelne Transkript-Datei."""
    print(f"Verarbeite Transkript: {file_path}")
    
    try:
        # Transkript laden
        transcript_data = load_transcript(file_path)
        
        # Mit Gemini API analysieren (erste Analyse)
        initial_analysis = analyze_transcript_with_gemini(client, transcript_data)
        
        if not initial_analysis:
            print(f"Warnung: Keine gültigen Analyseergebnisse für {file_path}")
            return False
        
        # Zweite Analyse (Korrekturlesen) mit Gemini Pro
        final_analysis = proofread_analysis_with_gemini(client, initial_analysis, transcript_data)
        
        # Ausgabedaten erstellen
        output_data = create_output_data(transcript_data, final_analysis)
        
        if not output_data:
            print(f"Warnung: Keine gültigen Ausgabedaten für {file_path}")
            return False
        
        # Ausgabedatei speichern
        output_filename = get_output_filename(file_path)
        output_path = os.path.join(output_dir, output_filename)
        save_output_data(output_data, output_path)
        
        return True
        
    except Exception as e:
        print(f"Fehler bei der Verarbeitung von {file_path}: {e}")
        return False

def main():
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
    
    print(f"Gefundene Transkript-Dateien: {len(transcript_files)}")
    
    # Transkripte verarbeiten
    success_count = 0
    for file_path in transcript_files:
        if process_transcript(client, file_path, args.output_dir):
            success_count += 1
    
    print(f"Verarbeitung abgeschlossen. {success_count} von {len(transcript_files)} Transkripten erfolgreich verarbeitet.")

if __name__ == "__main__":
    main() 