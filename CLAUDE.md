# MolDB

Offline molecule database: FastAPI + SQLite (SQLModel) + RDKit, vanilla JS UI with vendored Ketcher, shipped as a PyInstaller exe for Windows.

## Layout
- `moldb/` — core library (`database.py`, `chem.py`, `search.py`, `models.py`). Note: a venv is currently committed under `moldb/bin` and `moldb/lib`; never edit those (see #5).
- `ui/app.py` — FastAPI app; `ui/static/` — `index.html`, `app.js`, `style.css`, `ketcher/` (vendored build, do not edit).
- `build/moldb.spec` + `build/hooks/` — PyInstaller.
- `run.py` — entry point (dev and frozen).

## Commands
- Tests: `pytest tests/`
- Run: `python run.py` (http://127.0.0.1:8000)
- Build exe: `cd build && pyinstaller moldb.spec --clean`

## Non-negotiables
- **Security first**: databases hold confidential structures. Treat every DB value as untrusted (escape before HTML), validate all API input, never return raw exception text or absolute paths, never commit DB files.
- **Offline**: no CDN, telemetry or runtime network calls. Every asset must be served locally.
- **Windows frozen exe**: never resolve user data against `__file__`/`sys._MEIPASS`; always `encoding="utf-8"`; dispose SQLite engines before files are moved or deleted; when adding imports, check the PyInstaller spec.
- Version bumps must update `pyproject.toml` and `ui/app.py` together.

Use the `security-checklist` skill before opening a PR, and the `moldb-security-reviewer` agent for reviews.
