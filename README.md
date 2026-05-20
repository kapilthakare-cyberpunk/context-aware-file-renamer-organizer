# Context-Aware File Renamer & Organizer

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-171717?style=flat-square&logo=python&logoColor=D4AF37)
![License](https://img.shields.io/badge/License-MIT-171717?style=flat-square)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-171717?style=flat-square&logoColor=D4AF37)
![Groq](https://img.shields.io/badge/Groq-API-171717?style=flat-square&logoColor=D4AF37)
![Mistral](https://img.shields.io/badge/Mistral-API-171717?style=flat-square&logoColor=D4AF37)
![GUI](https://img.shields.io/badge/GUI-Floating_App-171717?style=flat-square&logoColor=D4AF37)
![Status](https://img.shields.io/badge/Status-Active-D4AF37?style=flat-square)

**An AI-powered floating desktop app that silently watches your folders, learns your file patterns, and renames + reorganizes everything with surgical precision.**

[Features](#features) · [Installation](#installation) · [Usage](#usage) · [LLM Backends](#llm-backends) · [Contributing](#contributing)

</div>

---

## About

Context-Aware File Renamer & Organizer is a lightweight floating GUI application that runs quietly in the background, observing your file system activity over hours or days. It builds a contextual understanding of your files — their content, naming patterns, creation dates, and relationships — then uses a multi-LLM engine (Ollama, Groq, Mistral) to make informed decisions about renaming and reorganizing them.

Unlike rule-based renamers, this tool **understands context**. It reads file metadata, infers purpose from content snippets, and applies consistent naming conventions across your entire workspace — without you lifting a finger.

### How It Works

```
Folders → Watcher Engine → Context Buffer → LLM Engine → Rename/Reorganize Engine → Clean Files
              (hours/days)     (patterns)    (decisions)        (safe apply)
```

1. **Watch** — monitors one or more folders continuously using filesystem events
2. **Collect** — builds a context buffer of file metadata, access patterns, and content hints
3. **Analyze** — feeds context to your chosen LLM (local Ollama or cloud Groq/Mistral)
4. **Decide** — the renaming engine proposes changes with confidence scores
5. **Apply** — changes are previewed in the floating GUI before any file is touched

---

## Features

- **Floating always-on-top GUI** — minimal, non-intrusive, stays out of your way
- **Multi-LLM backend** — switch between Ollama (local/private), Groq (fast), or Mistral (smart)
- **Long-running watcher** — observe folders for hours or days before acting
- **Context-aware decisions** — understands file relationships, not just names
- **Safe apply** — preview all changes before committing; full undo support
- **Batch operations** — rename and reorganize hundreds of files in one pass
- **Custom rules** — define naming conventions and folder structures per project
- **Zero cloud dependency** — run fully offline with Ollama

---

## Installation

```bash
git clone https://github.com/your-username/context-aware-file-renamer-organizer.git
cd context-aware-file-renamer-organizer
pip install -e .
```

Copy and configure environment:

```bash
cp .env.example .env
# Edit .env with your API keys
```

---

## Usage

```bash
# Launch the floating GUI
python -m renamer.gui

# CLI: watch a folder and analyze
python -m renamer watch ~/Downloads --llm ollama --model llama3.2

# CLI: dry-run rename proposals
python -m renamer analyze ~/Documents --dry-run
```

---

## LLM Backends

| Backend | Mode | Speed | Privacy | Setup |
|---------|------|-------|---------|-------|
| **Ollama** | Local | Medium | ✅ Full | `ollama pull llama3.2` |
| **Groq** | Cloud | ⚡ Fast | API key | `GROQ_API_KEY=...` |
| **Mistral** | Cloud | Fast | API key | `MISTRAL_API_KEY=...` |

Configure in `.env` or switch live in the GUI.

---

## Project Structure

```
src/renamer/
├── watcher/      # Filesystem event monitoring
├── llm/          # Ollama / Groq / Mistral adapters
├── engine/       # Rename & reorganize logic
└── gui/          # Floating tkinter/customtkinter app
tests/
docs/
.github/workflows/
```

---

## Contributing

PRs welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and open an issue before large changes.

---

## License

MIT © 2026
