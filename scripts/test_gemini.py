#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import google.generativeai as genai
import json

def test_gemini_api():
    """Tests the Gemini API connection and response parsing."""
    
    # API-Schlüssel aus Umgebungsvariable auslesen
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("FEHLER: GEMINI_API_KEY Umgebungsvariable ist nicht gesetzt")
        return False
    
    # Gemini-Client initialisieren
    genai.configure(api_key=api_key)
    
    # Einfacher Test-Prompt
    test_prompt = """
    Antworte mit einem validen JSON-Objekt, das folgender Struktur entspricht:
    
    ```json
    {
      "test": "erfolgreich",
      "version": "1.0",
      "beispiel_daten": [
        {
          "name": "Test 1",
          "wert": 42
        },
        {
          "name": "Test 2",
          "wert": 23
        }
      ]
    }
    ```
    """
    
    # Gemini-Konfiguration
    model_name = "gemini-2.0-flash-thinking-exp-01-21"
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 1024,
    }
    
    safety_settings = [
        {
            "category": "HARM_CATEGORY_CIVIC_INTEGRITY",
            "threshold": "BLOCK_NONE",
        }
    ]
    
    try:
        # Modell abrufen
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Anfrage stellen
        response = model.generate_content(test_prompt)
        
        print("Gemini API-Antwort erhalten:")
        print(f"{response.text}\n")
        
        # JSON aus der Antwort extrahieren
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', response.text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            # Falls kein Markdown-Block gefunden wurde, versuchen wir, die gesamte Antwort zu parsen
            json_text = response.text
        
        # JSON parsen
        result = json.loads(json_text)
        print("JSON erfolgreich geparst:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return True
        
    except Exception as e:
        print(f"FEHLER bei der Gemini API-Anfrage: {e}")
        return False

if __name__ == "__main__":
    print("Teste Gemini API-Verbindung...")
    if test_gemini_api():
        print("\nTest ERFOLGREICH! Die Gemini API funktioniert wie erwartet.")
    else:
        print("\nTest FEHLGESCHLAGEN! Bitte überprüfe die API-Konfiguration und den API-Schlüssel.") 