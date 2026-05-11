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

## Database & Shared Storage Considerations

MolDB uses a single SQLite `.sqlite` file as its database. This works well for single-user, local use — but comes with important caveats depending on how the file is accessed and where it is stored.

**SQLite relies on file-system locking to prevent concurrent write corruption.** Network file systems (Samba/CIFS, NFS, etc.) are notoriously unreliable at honoring these locks. On a Samba share in particular, byte-range locking is either broken or disabled by default on many configurations, which means two processes accessing the file simultaneously can silently corrupt the database — with no error shown to either user.

The key question is not *how many users* connect to MolDB, but *how many processes open the SQLite file simultaneously*. Because MolDB runs as a FastAPI/Uvicorn server, all browser sessions (users, tabs) go through that single process — SQLite's locking only needs to work within one process, which is always safe regardless of where the file lives.

**On local disk**, SQLite also handles multiple processes well in WAL mode: readers never block writers and writers never block readers. On a network share however, the OS-level locking primitives SQLite depends on to coordinate between processes are unreliable — a reader starting mid-commit can read a torn page even with a single writer.

| Setup | Safe? |
|---|---|
| One MolDB process, file on local disk, many browser users | ✅ Yes |
| One MolDB process, file on network share, many browser users | ✅ Yes — locking stays within one process |
| Multiple MolDB processes, file on local disk | ⚠️ Mostly OK in WAL mode |
| Multiple MolDB processes, file on network share | ❌ No — risk of silent corruption |

**Practical guidance:**
- **Single MolDB instance, local disk**: fully supported, no caveats.
- **Single MolDB instance, file on a network share**: safe for concurrent browser users, but keep backups — storage-level failures can still leave the database in a partial-write state.
- **Multiple MolDB instances sharing the same file**: not recommended over a network share. The correct solution is to migrate to a client-server database (PostgreSQL or MariaDB) and run a single shared MolDB service. The `MoleculeDB` class in `moldb/database.py` uses SQLModel/SQLAlchemy, so swapping the connection string from `sqlite:///path.sqlite` to `postgresql://...` requires only a one-line change plus adding the `psycopg2` driver.

If a multi-process deployment is needed short-term and write volume is low, you can reduce (but not eliminate) risk by enabling WAL mode: add `PRAGMA journal_mode=WAL;` on connection startup in `database.py`.


