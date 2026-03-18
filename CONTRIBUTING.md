# Contributing to Anon Protocol

First: thank you. This project exists because the problem it solves is real, and solving it well requires more perspectives than one person can hold.

---

## What We Need Most

### 1. Real-world testing
Run Anon Protocol on actual documents (anonymized samples are fine) and report what it gets wrong. False positives, missed entities, broken formatting — all of it is useful.

Open an issue with:
- Document type (DOCX, PDF, image)
- Language/dialect (Brazilian Portuguese, European Portuguese, etc.)
- What was missed or incorrectly flagged
- A sanitized sample if possible

### 2. NLP improvements
The current entity detection uses `spaCy pt_core_news_lg`. If you have experience with NLP and Portuguese, there is significant room to improve:
- Custom entity rules for Brazilian legal terminology
- Better handling of unusual proper names
- Disambiguation between legal acronyms and person/org names

### 3. New format support
Current gaps:
- `.odt` (LibreOffice)
- `.rtf`
- `.eml` (email files)
- Scanned PDFs with mixed text/image pages

### 4. Language support
Anonymization for documents in other languages (English, Spanish) requires different spaCy models and regex patterns. Contributions for multilingual support are welcome.

### 5. Documentation
If you are a lawyer or legal tech professional and you see gaps in how the tool is described or used — open an issue. Real-world use informs better documentation.

---

## How to Contribute Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test with at least one DOCX and one PDF
5. Open a pull request with a clear description of what changed and why

---

## Principles

This project has a clear philosophical position (see [PHILOSOPHY.md](PHILOSOPHY.md)). Contributions should align with it:

- **Local-first.** No network calls during anonymization. Ever.
- **No hidden dependencies.** Every package must be auditable.
- **Transparency over magic.** The map file must remain human-readable JSON.
- **Plain output.** No unnecessary formatting in the restored text.

---

## Reporting Issues

Use GitHub Issues. Include:
- Python version
- Operating system
- Document type and approximate size
- Full error message or traceback

---

## Code of Conduct

Be direct. Be technical. Be respectful. That's it.

---

*Lucas Gabriel Ramilo — lucasramiloadv@gmail.com*
