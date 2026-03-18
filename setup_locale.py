#!/usr/bin/env python3
"""
Anon Protocol — Locale Setup
Asks for country, uses Claude to research local patterns, generates config.json
"""

import os
import json
import sys
import subprocess
from pathlib import Path

BANNER = """
╔═══════════════════════════════════════════════╗
║        ANON PROTOCOL — LOCALE SETUP           ║
║   Configuring for your country automatically  ║
╚═══════════════════════════════════════════════╝
"""

RESEARCH_PROMPT = """You are configuring Anon Protocol — a document anonymization pipeline for AI-assisted legal work.

The user is in: {country}

Research and return a JSON configuration for this country with exactly this structure:

{{
  "country": "<country name in English>",
  "language": "<language name in English>",
  "locale_code": "<ISO 639-1 language code, e.g. pt, en, es, fr>",
  "spacy_model": "<best available spaCy model for this language, e.g. pt_core_news_lg, en_core_web_lg, es_core_news_lg>",
  "spacy_model_url": "<direct pip install URL for the spaCy model from GitHub releases, or empty string if installable via spacy download>",
  "ocr_language": "<tesseract language code, e.g. por, eng, spa, fra>",
  "patterns": {{
    "<ENTITY_TYPE>": "<Python regex pattern as a raw string>"
  }},
  "preserve": [
    "<list of legal acronyms, court names, government agencies, state/region codes that must NEVER be anonymized>"
  ],
  "claude_instruction": "<A concise instruction in the local language explaining to an AI assistant what the [[PLACEHOLDER_N]] tokens mean in anonymized documents, and how to process them correctly. 3-5 sentences.>"
}}

Rules:
- patterns must cover all government-issued ID numbers, tax IDs, registration numbers, phone formats, postal codes, email, and legal process numbers used in {country}
- preserve must include all common legal/judicial acronyms, court abbreviations, agency names, and administrative region codes
- spacy_model must be a real, currently available spaCy model
- claude_instruction must be written in the local language of {country}
- Return ONLY valid JSON, no markdown, no explanation, no code blocks
"""


def get_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print("\nANTHROPIC_API_KEY not found in environment.")
        print("Get your key at: https://console.anthropic.com")
        key = input("Paste your API key: ").strip()
        if not key:
            print("Error: API key required.")
            sys.exit(1)
    return key


def research_locale(country, api_key):
    import anthropic
    print(f"\n[setup] Asking Claude to research '{country}' patterns...")
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": RESEARCH_PROMPT.format(country=country)
            }
        ]
    )
    return message.content[0].text.strip()


def install_spacy_model(model_name, model_url):
    print(f"\n[setup] Installing spaCy model: {model_name}")
    if model_url:
        cmd = [sys.executable, "-m", "pip", "install", model_url, "--break-system-packages"]
    else:
        cmd = [sys.executable, "-m", "spacy", "download", model_name]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[setup] Model installed successfully.")
    else:
        print(f"[setup] Warning: could not install model automatically.")
        print(f"        Run manually: pip install {model_url or model_name}")


def save_config(config, path="config.json"):
    Path(path).write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[setup] Configuration saved to {path}")


def print_claude_instruction(config):
    print("\n" + "─" * 50)
    print("INSTRUCTION FOR YOUR AI ASSISTANT")
    print("─" * 50)
    print(config.get("claude_instruction", ""))
    print("─" * 50)
    print("\nThis instruction is also saved in config.json.")
    print("Add it as a system prompt when using Anon Protocol with any AI assistant.")


def main():
    print(BANNER)

    country = input("What country are you in? (e.g. Brazil, United States, Portugal): ").strip()
    if not country:
        print("Error: country is required.")
        sys.exit(1)

    api_key = get_api_key()

    try:
        raw = research_locale(country, api_key)
        config = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"\n[setup] Error parsing Claude response: {e}")
        print("Raw response:")
        print(raw)
        sys.exit(1)
    except Exception as e:
        print(f"\n[setup] Error: {e}")
        sys.exit(1)

    print(f"\n[setup] Locale detected:")
    print(f"  Country:      {config.get('country')}")
    print(f"  Language:     {config.get('language')}")
    print(f"  spaCy model:  {config.get('spacy_model')}")
    print(f"  OCR language: {config.get('ocr_language')}")
    print(f"  Patterns:     {len(config.get('patterns', {}))} entity types")
    print(f"  Preserve:     {len(config.get('preserve', []))} terms")

    install = input("\nInstall spaCy model now? (Y/n): ").strip().lower()
    if install != "n":
        install_spacy_model(config["spacy_model"], config.get("spacy_model_url", ""))

    save_config(config)
    print_claude_instruction(config)

    print("\n[setup] Done. Run anon_protocol.py to start anonymizing documents.")


if __name__ == "__main__":
    main()
