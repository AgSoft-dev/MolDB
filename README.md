# MolDB — Local Molecule Database

A fully offline Python + web UI application for managing a chemistry molecule database.

## Quick Start

### 1. Install dependencies

```bash
# Recommended: use conda for RDKit
conda create -n moldb python=3.11 rdkit -c conda-forge -y
conda activate moldb
pip install -r requirements.txt
```

### 2. Run the app

```bash
python run.py
# Opens http://localhost:8000 in your browser automatically
```

The SQLite database is not created automatically unless you explicitly create one in advanced mode. On first run, use the UI to select an existing `.sqlite` file or, in advanced mode, create a new database and apply schema migration. The `MOLDB_PATH` environment variable is optional and only useful for development; packaged executables should use the UI file picker instead.

### 3. Run tests

```bash
pytest tests/
```

---

## Features

- Add / edit / delete molecules
- Search by name (fuzzy), CAS number, exact SMILES
- Structure similarity search (Tanimoto) and substructure search via Kekule.js drawing widget
- 2D structure visualization (RDKit SVG rendering)
- Duplicate detection via InChIKey

## Build Windows .exe

```bash
conda activate moldb
pip install pyinstaller
cd build
pyinstaller moldb.spec --clean
# Output: build/../dist/MolDB.exe
```

## Project Structure

```
moldb/          # Core library (importable)
ui/             # FastAPI app + static frontend
tests/          # Pytest suite
build/          # PyInstaller spec + RDKit hooks
run.py          # Entrypoint
```

## API Docs

Run the app and visit [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI + Uvicorn |
| Database | SQLite via SQLModel |
| Chemistry | RDKit |
| Structure editor | Kekule.js |
| Frontend | Vanilla JS |
| Packaging | PyInstaller |
