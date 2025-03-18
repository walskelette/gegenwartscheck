# Gegenwartscheck Prompt Improvement Specification

This document details recommendations for improving the prompts used in the Gemini Analyzer to extract more accurate and consistent results from podcast transcripts.

## Analysis of Current Prompts

### Current Main Analysis Prompt

The current main analysis prompt has several strengths:

1. Provides good background information about the podcast and the "Gegenwartscheck" segment
2. Clearly defines the required fields for extraction
3. Includes specific instructions about the expected JSON format
4. Attempts to guide the model to identify key phrases that signal the start of a Gegenwartscheck

However, it also has some limitations:

1. Lacks specific examples to guide pattern recognition
2. Uses vague descriptions for some fields (like "metaebene")
3. Doesn't account for variations in how speakers might introduce or discuss Gegenwartscheck items
4. Doesn't provide guidance on handling partially missing information
5. Could be more explicit about mapping speakers (SPEAKER_X) to podcast hosts (Nina, Lars, Ijoma)

### Current Proofreading Prompt

The proofreading prompt is better structured but also has limitations:

1. Focuses primarily on spelling corrections rather than content validation
2. Doesn't verify the extraction logic itself
3. Doesn't provide clear examples of what to correct vs. what to leave alone

## Improved Prompt Design

### Main Analysis Prompt Improvements

#### 1. Add Clear Pattern Recognition Instructions

```
# Erkennungsmuster für Gegenwartsvorschläge
Gegenwartsvorschläge werden oft mit bestimmten Phrasen eingeleitet:
- "Ich habe als Gegenwartscheck (mitgebracht)..."
- "Mein Gegenwartscheck ist/wäre..."
- "Ich hätte als Gegenwartscheck..."
- "Für den Gegenwartscheck schlage ich vor..."
- "Ich habe für den Gegenwartscheck..."
- "Als Gegenwartscheck würde ich vorschlagen..."
```

#### 2. Add Speaker Mapping Instructions

```
# Zuordnung der Sprecher zu Podcast-Hosts
Im Transkript werden die Sprecher als SPEAKER_X bezeichnet. 
- Versuche, die Sprecher anhand des Kontexts und der Namen in den Gesprächen zuzuordnen
- Beachte, dass meist Nina Pauer, Lars Weisbrod und Ijoma Mangold an den Gesprächen teilnehmen
- Wenn Hörer-Vorschläge diskutiert werden, wird der Name oft im Kontext genannt
```

#### 3. Add Examples from Previous Analyses

```
# Beispiel für einen extrahierten Gegenwartsvorschlag
Aus einem Transkript:
SPEAKER_1: "Ich habe als Gegenwartscheck mitgebracht: Plateau-Stiefel! Sie sind diesen Winter der Trend bei Frauen, und zusammen mit diesen Space-Iglus vor Restaurants entsteht eine Art Mondlandschaft."
SPEAKER_2: "Ja, das ist interessant, vor allem als Vorbereitung auf die nächsten Mondmissionen."
SPEAKER_3: "Dafür kriegst du einen Punkt von mir."

Extrahiertes Ergebnis:
{
  "vorschlag": "Plateau-Stiefel",
  "vorschlagender": "Lars",
  "ist_hoerer": false,
  "hoerer_name": null,
  "begruendung": "Bestimmte Stiefel mit Plateausohle sind Schuhtrend bei Frauen diesen Winter. In Kombination mit Space-Iglus vor Restaurants entsteht eine Mondlandschaft.",
  "metaebene": "Vorbereitung auf die nächsten Mondmissionen",
  "punkt_erhalten": true,
  "punkt_von": "Ijoma",
  "tags": ["Mode", "Schuhe", "Winter", "Mond", "Raumfahrt"],
  "start_zeit": "00:03:48",
  "ende_zeit": "00:06:56"
}
```

#### 4. Clarify Field Definitions

```
# Detaillierte Feldbeschreibungen
- vorschlag: Der Kern-Begriff oder die Idee, die als gegenwärtig vorgeschlagen wird. Nur der Name ohne weitere Erklärungen.
- begruendung: Die vollständige Erläuterung, warum der Vorschlag gegenwärtig ist.
- metaebene: Ein weiterer Kontext oder eine übergeordnete Bedeutung, die explizit erwähnt wird. Nur ausfüllen, wenn klar als Metaebene benannt.
- tags: 3-5 präzise Schlagwörter, die den thematischen Bereich des Vorschlags erfassen.
```

#### 5. Add Instructions for Handling Partial Information

```
# Umgang mit unvollständigen Informationen
- Wenn das Transkript unvollständig ist oder Informationen fehlen, verwende null als Wert.
- Spekuliere nicht über fehlende Informationen, sondern dokumentiere nur, was klar im Transkript erkennbar ist.
- Bei unklaren Punktvergaben: Setze punkt_erhalten = false und punkt_von = null.
```

### Focused Proofreading Prompt (Spelling Corrections Only)

Per user requirements, the proofreading prompt has been refocused to perform only spelling corrections using Google Grounding, without making any content-related changes.

#### 1. Clear Focused Instructions

```
# Aufgabe
Deine Aufgabe ist AUSSCHLIESSLICH die Überprüfung der Rechtschreibung von Konzepten, Marken und Fachbegriffen:

1. Überprüfe für jeden extrahierten "vorschlag" und jedes wichtige Konzept in der "begruendung", ob die Schreibweise korrekt ist.
2. Nutze IMMER das Google-Grounding-Tool, um die korrekte Schreibweise zu verifizieren.
3. Korrigiere falsch geschriebene Konzepte, Marken, Namen und Fachbegriffe.
```

#### 2. Explicit Limitations

```
# Wichtige Einschränkungen
1. Ändere KEINE inhaltlichen Aspekte der Analyse.
2. Verändere NICHT die grundlegende Struktur oder Bedeutung der Daten.
3. Füge KEINE neuen Tags hinzu und ändere die Tags nur, wenn sie falsch geschrieben sind.
4. Erweitere NICHT die "begruendung" oder andere Textfelder inhaltlich.
5. Übersetze KEINE Inhalte ins Englische - behalte alle deutschen Texte unverändert bei.
```

#### 3. Simple Example

```
# Beispiel für eine Rechtschreibkorrektur
Vor der Korrektur:
{
  "vorschlag": "KI-generierte Pintrest-Bilder"
}

Nach der Korrektur:
{
  "vorschlag": "KI-generierte Pinterest-Bilder"
}
```

## Temperature and Parameter Settings

### Recommendations for Analysis Settings

For the initial analysis:
- temperature: 0.1 (reduced from 0.2)
- top_p: 0.9
- top_k: 40
- max_output_tokens: 4096

Rationale: Lower temperature will lead to more consistent, deterministic results, which is important for the initial extraction to follow the specified pattern more precisely.

### Recommendations for Proofreading Settings

For the proofreading phase:
- temperature: 0.2 (increased from 0.1)
- top_p: 0.95
- top_k: 40
- max_output_tokens: 4096

Rationale: Slightly higher temperature allows more creativity in the proofreading phase to identify and correct spelling errors that might require some creative thinking, while still maintaining focus on the single task of spelling correction.

## Implementation Plan

1. Update the `create_gemini_prompt` function in `gemini_analyzer.py` with the improved main analysis prompt
2. Update the `proofread_analysis_with_gemini` function with the focused spelling-correction prompt
3. Adjust the temperature and parameter settings as recommended
4. Run tests on a sample of transcripts to compare results
5. Iterate on prompt design based on error analysis
6. Deploy the improved prompts to production

## Open Questions

1. Is there a more effective way to map SPEAKER_X identifiers to actual podcast hosts?
2. Should we consider using a more structured approach like Chain-of-Thought for the main analysis?
3. Would a dedicated NER (Named Entity Recognition) step before the main analysis improve accuracy?
4. Should we use different prompt designs for different episode formats or special episodes?
5. How can we better handle episodes where no clear Gegenwartscheck segments exist?

## Success Metrics

We'll evaluate the success of these prompt improvements by:

1. Accuracy: Percentage of correctly extracted Gegenwartscheck items
2. Correctness: Percentage of correctly spelled concepts, brands, and terms
3. Consistency: Variation in output quality across different episodes
4. Error rate: Reduction in common spelling error patterns

## Next Steps

After implementing these prompt improvements, we should:

1. Create a systematic evaluation process for prompt quality
2. Build a test suite with known ground truth examples
3. Consider implementing a more comprehensive content validation step later, after the spelling correction is working well
4. Explore using RLHF (Reinforcement Learning from Human Feedback) to continually optimize prompt design 