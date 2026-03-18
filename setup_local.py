#!/usr/bin/env python3
"""
Anon Protocol — Local Setup
Generates a prompt for the user to paste into Claude, then saves the config.json response.
"""

import json
import sys
from pathlib import Path

BANNER = """
╔═══════════════════════════════════════════════╗
║        ANON PROTOCOL — LOCAL SETUP            ║
║   Configuring for your country automatically  ║
╚═══════════════════════════════════════════════╝
"""

PROMPT_TEMPLATE = """I am setting up Anon Protocol — a document anonymization pipeline for AI-assisted legal work.

My country is: {country}

Please return a JSON configuration for this country with exactly this structure:

{{
  "country": "<country name in English>",
  "language": "<language name in English>",
  "locale_code": "<ISO 639-1 language code, e.g. pt, en, es, fr>",
  "spacy_model": "<best available spaCy model for this language, e.g. pt_core_news_lg, en_core_web_lg, es_core_news_lg>",
  "spacy_model_url": "<direct pip install URL for the spaCy model from GitHub releases, or empty string if installable via spacy download>",
  "ocr_language": "<tesseract language code, e.g. por, eng, spa, fra>",
  "patterns": {{
    "<ENTITY_TYPE>": "<Python regex pattern>"
  }},
  "preserve": [
    "<legal acronyms, court names, government agencies, state/region codes that must NEVER be anonymized>"
  ],
  "claude_instruction": "<A concise instruction in the local language of {country} explaining to an AI assistant what the [[PLACEHOLDER_N]] tokens mean in anonymized documents, and how to process them correctly. 3-5 sentences.>"
}}

Rules:
- patterns must cover all government-issued ID numbers, tax IDs, registration numbers, phone formats, postal codes, email, and legal process numbers used in {country}
- preserve must include all common legal/judicial acronyms, court abbreviations, agency names, and administrative region codes
- spacy_model must be a real, currently available spaCy model
- claude_instruction must be written in the local language of {country}
- Return ONLY valid JSON, no explanation, no code blocks
"""


def main():
    print(BANNER)

    country = input("What country are you in? (e.g. Brazil, United States, Portugal): ").strip()
    if not country:
        print("Error: country is required.")
        sys.exit(1)

    prompt = PROMPT_TEMPLATE.format(country=country)

    print("\n" + "═" * 60)
    print("STEP 1 — Copy the prompt below and paste it into Claude:")
    print("═" * 60)
    print(prompt)
    print("═" * 60)

    print("\nSTEP 2 — Paste Claude's JSON response below.")
    print("When done, type END on a new line and press Enter:\n")

    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)

    raw = "\n".join(lines).strip()

    # Remove markdown code blocks if present
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
    if raw.endswith("```"):
        raw = "\n".join(raw.split("\n")[:-1])
    raw = raw.strip()

    try:
        config = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"\nError: could not parse JSON — {e}")
        print("Make sure you copied the full response from Claude.")
        sys.exit(1)

    config_path = Path(__file__).parent / "config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[setup] Configuration saved to config.json")
    print(f"  Country:      {config.get('country')}")
    print(f"  Language:     {config.get('language')}")
    print(f"  spaCy model:  {config.get('spacy_model')}")
    print(f"  OCR language: {config.get('ocr_language')}")
    print(f"  Patterns:     {len(config.get('patterns', {}))} entity types")
    print(f"  Preserve:     {len(config.get('preserve', []))} terms")

    print("\n" + "─" * 60)
    print("INSTRUCTION FOR YOUR AI ASSISTANT:")
    print("─" * 60)
    print(config.get("claude_instruction", ""))
    print("─" * 60)

    print("\n[setup] Done. Run anon_protocol.py to start anonymizing documents.")


if __name__ == "__main__":
    main()
