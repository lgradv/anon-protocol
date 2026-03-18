# Anon Protocol

**Privacy-first document anonymization for AI-assisted legal work.**

> *"Behind the veil of ignorance, no one knows their place in society. The principles of justice are chosen without anyone knowing their situation."*
> — John Rawls, A Theory of Justice (1971)

---

## The Problem

AI assistants are transforming legal work — reviewing contracts, drafting clauses, analyzing disputes. But every document you send to a cloud AI carries your client's name, CPF, CNPJ, address, medical history, financial data.

You don't control what happens to that data. You don't know if it's stored. You don't know if it's used for training. You just hope for the best — and hope is not a compliance strategy.

The legal profession has a duty of confidentiality that predates AI by centuries. That duty doesn't pause when you open a chat window.

**There had to be a better way.**

---

## The Solution

Anon Protocol is a local pipeline that strips sensitive data from documents *before* they reach any AI — and puts it back *after* the AI returns its output.

The AI never sees the real data. It receives placeholders:

```
[[PESSOA_1]] assinou o contrato da empresa com CNPJ [[CNPJ_1]],
situada na [[LOCAL_1]], nº 131, [[LOCAL_2]] – PR.
```

A local map file — never leaving your machine — holds the real values:

```json
{
  "[[PESSOA_1]]": "João da Silva",
  "[[CNPJ_1]]": "12.345.678/0001-90",
  "[[LOCAL_1]]": "Rua das Flores",
  "[[LOCAL_2]]": "Pato Branco"
}
```

After the AI finishes, Anon Protocol restores the original data into the final output. You get the full result. The AI never got the real information.

---

## Philosophy

The name is a direct reference to John Rawls' **Veil of Ignorance** — one of the foundational concepts of modern political philosophy.

Rawls argued that just decisions are made when decision-makers cannot identify who is affected by them. Remove identity, and bias follows.

We applied this to AI-assisted legal work: when an AI cannot identify the parties in a document, it can only analyze the structure, the law, the clauses — not the person. The analysis becomes purely technical. Truly neutral.

This is not just a privacy tool. It is a philosophical position: **AI should reason about law, not about people.**

---

## How It Works

```
[original document]
        ↓
   1. TEXT EXTRACTION
      .docx → python-docx
      .pdf  → pdfplumber (OCR fallback for scanned pages)
      .png/.jpg → pytesseract (OCR)
        ↓
   2. ENTITY DETECTION
      Structured data → regex (CPF, CNPJ, phone, date, email, process number)
      Names & orgs    → spaCy pt_core_news_lg (local NLP, no API calls)
        ↓
   3. MAPPING
      Builds placeholder ↔ real value dictionary
      Saved locally as map_FILENAME_TIMESTAMP.json
        ↓
   4. ANONYMIZATION
      Replaces all sensitive values with placeholders
      Word-boundary aware — never corrupts partial matches
        ↓
   [AI receives anonymized text]
        ↓
   5. AI DOES ITS WORK
        ↓
   6. RESTORATION
      Placeholders replaced with real values
      Clean plain text output — no formatting noise
        ↓
[final document with real data]
```

**Everything runs locally.** No API calls during anonymization. No data leaves your machine. The only thing that touches the cloud is the anonymized text — which contains no real identities.

---

## Detected Entity Types

| Type | Method | Examples |
|---|---|---|
| `CPF` | regex | 000.000.000-00 |
| `CNPJ` | regex | 00.000.000/0001-00 |
| `CEP` | regex | 00000-000 |
| `TELEFONE` | regex | (41) 99999-9999 |
| `DATA` | regex | 01/01/2025 |
| `EMAIL` | regex | name@domain.com |
| `OAB` | regex | OAB/PR 12345 |
| `PROCESSO` | regex | 0000000-00.0000.0.00.0000 |
| `PESSOA` | NLP (spaCy) | João da Silva |
| `ORGANIZACAO` | NLP (spaCy) | Escritório Ramilo & Associados |
| `LOCAL` | NLP (spaCy) | Rua das Flores, Pato Branco |

Legal acronyms and abbreviations (LGPD, CLT, OAB, STJ, state codes, etc.) are preserved and never anonymized.

---

## Installation

**Requirements:** Python 3.9+, Tesseract OCR

```bash
# 1. Clone
git clone https://github.com/lucasramiloadv/anon-protocol.git
cd anon-protocol

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install the Portuguese NLP model (runs locally — ~570MB)
pip install https://github.com/explosion/spacy-models/releases/download/pt_core_news_lg-3.8.0/pt_core_news_lg-3.8.0-py3-none-any.whl

# 4. Install Tesseract OCR (for scanned PDFs and images)
# Ubuntu/Debian:
sudo apt install tesseract-ocr tesseract-ocr-por

# macOS:
brew install tesseract
```

---

## Usage

### Anonymize a document

```bash
python3 anon_protocol.py path/to/document.pdf
```

Output:
- Anonymized text printed to stdout
- `map_FILENAME_TIMESTAMP.json` saved next to the original file
- `anon_FILENAME_TIMESTAMP.txt` saved next to the original file

### Restore real data after AI processing

```bash
python3 anon_protocol.py --revert map_contract_20260318.json ai_result.txt
```

Output:
- Final document with real data restored, printed to stdout

### Integration with Claude Code

When using Claude Code as your AI assistant, the workflow becomes seamless:

1. Send the document path with `-anon` flag to Claude
2. Claude runs the anonymization pipeline automatically
3. Claude processes the anonymized text
4. Claude runs the revert step and delivers the final output

No manual steps. No copy-paste. The protocol is invisible.

---

## Supported Formats

| Format | Method |
|---|---|
| `.docx` | python-docx |
| `.pdf` (digital) | pdfplumber |
| `.pdf` (scanned) | pdfplumber + pytesseract OCR |
| `.png`, `.jpg`, `.jpeg` | pytesseract OCR |
| `.bmp`, `.tiff`, `.webp` | pytesseract OCR |
| `.txt` | direct read |

---

## What Is NOT Anonymized

The following are intentionally preserved:

- Brazilian legal acronyms: LGPD, CLT, STF, STJ, TST, OAB, ANS...
- Corporate suffixes: LTDA, S.A., ME, EIRELI...
- Brazilian state codes: SP, RJ, MG, PR, SC, RS...
- Numbers that are not structured identifiers

---

## Limitations

- NLP-based detection (names, organizations) depends on context quality. Unusual names or informal writing may reduce accuracy.
- Very large documents (100k+ characters) are processed in segments for NLP — regex detection covers the full text.
- Handwritten text in images requires high resolution scans for reliable OCR.
- The tool anonymizes. It does not guarantee legal compliance by itself — professional judgment is still required.

---

## Roadmap

- [ ] CLI installation via `pip install anon-protocol`
- [ ] Interactive review of detected entities before anonymization
- [ ] Support for `.odt` and `.rtf`
- [ ] English NLP model support
- [ ] Batch processing for multiple files
- [ ] Audit log for compliance documentation

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

If you are a lawyer, legal tech professional, or privacy researcher — open an issue and tell us how you use it. Real-world use cases improve detection accuracy.

---

## Author

**Lucas Gabriel Ramilo**
Lawyer · Legal Tech · LGR Consultoria LTDA
[lucasramiloadv@gmail.com](mailto:lucasramiloadv@gmail.com)

---

## License

MIT License. See [LICENSE](LICENSE).

Use it, fork it, improve it. Privacy is a right, not a feature.
