#!/usr/bin/env python3
"""
Anon Protocol — Privacy-first document anonymization for AI-assisted legal work.
Author: Lucas Gabriel Ramilo <lucasramiloadv@gmail.com>
License: MIT
Version: 1.0.0

Philosophy: Inspired by John Rawls' Veil of Ignorance — fair decisions are made
when the decision-maker cannot identify who is behind the data.
"""

import sys
import re
import json
import os
from pathlib import Path
from datetime import datetime


BANNER = """
╔═══════════════════════════════════════════════╗
║           ANON PROTOCOL  v1.0.0               ║
║   Privacy-first anonymization for legal AI    ║
║   github.com/lucasramiloadv/anon-protocol     ║
╚═══════════════════════════════════════════════╝
"""

# ── Siglas e termos que NÃO devem ser anonimizados ────────────────────────────

PRESERVE = {
    # Leis e órgãos brasileiros
    "LGPD", "CLT", "CF", "STJ", "STF", "TST", "TRT", "TRF",
    "MPF", "MPT", "ANS", "ANATEL", "ANVISA", "BACEN", "CVM",
    "CADE", "TCU", "TCE", "OAB", "CFM", "CRM", "CRO", "CREA", "CFC",
    # Documentos e identificadores
    "CNPJ", "CPF", "RG", "CEP", "CEF", "BB", "FGTS", "INSS", "PIS",
    # Tipos societários
    "LTDA", "S.A", "SA", "ME", "EIRELI", "EPP",
    # Estados brasileiros
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}


# ── Padrões regex para dados estruturados ────────────────────────────────────

PATTERNS = {
    "CPF":      r"\b\d{3}[\.\s]?\d{3}[\.\s]?\d{3}[-\s]?\d{2}\b",
    "CNPJ":     r"\b\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[/\s]?\d{4}[-\s]?\d{2}\b",
    "CEP":      r"\b\d{5}-\d{3}\b",
    "TELEFONE": r"\b(\(?\d{2}\)?\s?)?(\d{4,5}[-\s]?\d{4})\b",
    "DATA":     r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b",
    "EMAIL":    r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b",
    "OAB":      r"\bOAB[\/\s]?[A-Z]{2}[\/\s]?\d+\b",
    "PROCESSO": r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b",
}


# ── Extração de texto por tipo de arquivo ────────────────────────────────────

def extract_docx(path):
    from docx import Document
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_pdf(path):
    import pdfplumber
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n".join(pages)


def extract_image(path):
    import pytesseract
    from PIL import Image
    img = Image.open(path)
    return pytesseract.image_to_string(img, lang="por")


def extract_scanned_pdf(path):
    import pytesseract, pdfplumber, io
    from PIL import Image
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            img = page.to_image(resolution=300).original
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            pil_img = Image.open(buf)
            pages.append(pytesseract.image_to_string(pil_img, lang="por"))
    return "\n".join(pages)


def extract_text(path):
    ext = Path(path).suffix.lower()
    log(f"Extracting from: {Path(path).name} ({ext})")

    if ext == ".docx":
        return extract_docx(path)

    elif ext == ".pdf":
        text = extract_pdf(path)
        if not text.strip():
            log("No text layer found — running OCR on PDF pages...")
            return extract_scanned_pdf(path)
        return text

    elif ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"):
        log("Image detected — running OCR...")
        return extract_image(path)

    else:
        return Path(path).read_text(encoding="utf-8", errors="ignore")


# ── Detecção de entidades ─────────────────────────────────────────────────────

def detect_regex(text):
    found = []
    for kind, pattern in PATTERNS.items():
        for m in re.finditer(pattern, text, re.IGNORECASE):
            found.append((kind, m.group(), m.start(), m.end()))
    return found


def detect_ner(text):
    import spacy
    log("Loading NLP model (pt_core_news_lg)...")
    nlp = spacy.load("pt_core_news_lg")
    doc = nlp(text[:100000])
    found = []
    label_map = {"PER": "PESSOA", "ORG": "ORGANIZACAO", "LOC": "LOCAL"}
    for ent in doc.ents:
        if ent.label_ not in label_map:
            continue
        val = ent.text.strip()
        if len(val) < 3:
            continue
        if val.upper() in PRESERVE:
            continue
        if re.match(r"^\d+$", val):
            continue
        found.append((label_map[ent.label_], val, ent.start_char, ent.end_char))
    return found


def build_map(text):
    all_entities = detect_regex(text) + detect_ner(text)
    all_entities.sort(key=lambda x: x[2])

    # Remove overlaps
    clean = []
    last_end = -1
    for item in all_entities:
        kind, val, start, end = item
        if start >= last_end and val.strip():
            clean.append(item)
            last_end = end

    # Build placeholder maps
    val_to_ph = {}
    ph_to_val = {}
    counters = {}

    for kind, val, _, _ in clean:
        key = val.strip()
        if key not in val_to_ph:
            counters[kind] = counters.get(kind, 0) + 1
            placeholder = f"[[{kind}_{counters[kind]}]]"
            val_to_ph[key] = placeholder
            ph_to_val[placeholder] = key

    log(f"Entities detected: {len(ph_to_val)}")
    return val_to_ph, ph_to_val


# ── Substituição e reversão ───────────────────────────────────────────────────

def replace_whole_word(text, value, substitute):
    escaped = re.escape(value)
    pattern = r'(?<![A-Za-zÀ-ÿ0-9])' + escaped + r'(?![A-Za-zÀ-ÿ0-9])'
    result = re.sub(pattern, substitute, text)
    if result == text:
        result = text.replace(value, substitute)
    return result


def anonymize(text, val_to_ph):
    for val in sorted(val_to_ph, key=len, reverse=True):
        text = replace_whole_word(text, val, val_to_ph[val])
    return text


def deanonymize(text, ph_to_val):
    for placeholder, val in ph_to_val.items():
        text = text.replace(placeholder, val)
    return text


# ── Limpeza de texto ─────────────────────────────────────────────────────────

def clean_text(text):
    lines = text.splitlines()
    result = []
    prev_blank = False
    for line in lines:
        line = line.strip()
        if not line:
            if not prev_blank:
                result.append("")
            prev_blank = True
        else:
            result.append(line)
            prev_blank = False
    return "\n".join(result).strip()


# ── Utilitários ───────────────────────────────────────────────────────────────

def log(msg):
    print(f"[anon-protocol] {msg}", file=sys.stderr)


def generate_output_paths(source_path):
    base = Path(source_path).stem
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    parent = Path(source_path).parent
    map_path = parent / f"map_{base}_{ts}.json"
    anon_path = parent / f"anon_{base}_{ts}.txt"
    return map_path, anon_path


# ── Comandos principais ───────────────────────────────────────────────────────

def cmd_anonymize(source_path):
    print(BANNER, file=sys.stderr)
    log(f"Source: {source_path}")

    text = extract_text(source_path)
    text = clean_text(text)

    val_to_ph, ph_to_val = build_map(text)
    anon_text = anonymize(text, val_to_ph)

    map_path, anon_path = generate_output_paths(source_path)
    map_path.write_text(json.dumps(ph_to_val, ensure_ascii=False, indent=2), encoding="utf-8")
    anon_path.write_text(anon_text, encoding="utf-8")

    log(f"Map saved:  {map_path}")
    log(f"Anon text:  {anon_path}")
    log("Done. Send the anonymized text to your AI assistant.")
    log(f"To restore: python3 anon_protocol.py --revert {map_path} <result.txt>")

    print(anon_text)


def cmd_revert(map_path, anon_path):
    print(BANNER, file=sys.stderr)
    ph_to_val = json.loads(Path(map_path).read_text(encoding="utf-8"))
    anon_text = Path(anon_path).read_text(encoding="utf-8")
    final = deanonymize(anon_text, ph_to_val)
    final = clean_text(final)
    log("Revert complete.")
    print(final)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) == 2:
        cmd_anonymize(sys.argv[1])
    elif len(sys.argv) == 4 and sys.argv[1] == "--revert":
        cmd_revert(sys.argv[2], sys.argv[3])
    else:
        print(BANNER)
        print("Usage:")
        print("  python3 anon_protocol.py <document>                      — anonymize")
        print("  python3 anon_protocol.py --revert <map.json> <anon.txt>  — restore")
        print()
        print("Supported formats: .docx  .pdf  .png  .jpg  .jpeg  .bmp  .tiff")
        sys.exit(1)


if __name__ == "__main__":
    main()
