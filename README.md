# MolDB — Local Molecule Database

<p align="center">
  <img src="docs/screenshots/banner.png" alt="MolDB Banner" width="900">
</p>

<p align="center">
  <strong>Fully Offline Molecule Database for Chemists</strong>
</p>

A fully offline Python + web UI application for managing a chemistry molecule database.

---

# Screenshots

## Molecule Browser and Structure Search

![MolDB Molecule Browser](docs/screenshots/molecule-browser.png)

> Browse, filter, and manage your local molecule collection with fast offline search.
> Perform exact, similarity, and substructure searches using the integrated structure editor.

---

## Molecule Detail View

![MolDB Molecule Detail](docs/screenshots/molecule-detail.png)

> Inspect molecular structures, identifiers, properties, and generated 2D depictions.

---

## Molecule Editor

![MolDB Molecule Editor](docs/screenshots/molecule-editor.png)

> Add or edit molecules with validation, duplicate detection, and RDKit-powered processing.

---

# Quick Start (Windows)

This guide explains step-by-step how to install Python and run the application on Windows.

## 1. Install Miniforge (recommended)

This project uses **RDKit**, which is much easier to install with **Conda**.  
We recommend using **Miniforge**, a lightweight Conda distribution.

### Download Miniforge

Go to:

https://github.com/conda-forge/miniforge/releases

Download:

- **Miniforge3-Windows-x86_64.exe** (for most Windows PCs)

### Install Miniforge

Run the installer and:

- Click **Next**
- Accept the license
- Choose **Just Me**
- Keep the default install location
- Recommended: enable **"Add Miniforge to PATH"**
- Finish installation

After installation, open:

- **Miniforge Prompt**  
  (from the Windows Start Menu)

---

## 2. Download the project

### Option A — Download ZIP (easiest)

On GitHub:

- Click the green **Code** button
- Click **Download ZIP**
- Extract the ZIP somewhere convenient

### Option B — Use Git

```bash
git clone https://github.com/yourname/yourproject.git
cd yourproject
```

---

## 3. Create the Python environment

In the **Miniforge Prompt**, navigate to the project folder.

Example:

```bash
cd C:\Users\YourName\Downloads\yourproject
```

Then create the environment:

```bash
conda create -n moldb python=3.11 rdkit -c conda-forge -y
```

This may take a few minutes the first time.

---

## 4. Activate the environment

Every time you want to run the app, activate the environment first:

```bash
conda activate moldb
```

You should now see `(moldb)` at the beginning of the command line.

---

## 5. Install project dependencies

Run:

```bash
pip install -r requirements.txt
```

---

## 6. Start the application

Run:

```bash
python run.py
```

Your browser should automatically open:

```text
http://localhost:8000
```

If it does not open automatically, copy the address above into your browser manually.

---

# Database setup

The SQLite database is **not created automatically** unless you explicitly create one in advanced mode.

On first launch:

- Use the interface to select an existing `.sqlite` database file

OR

- Use **Advanced Mode** to:
  - create a new database
  - apply the schema migration

---

## Optional: `MOLDB_PATH`

The `MOLDB_PATH` environment variable is optional.

It is mainly useful for development workflows.  
For normal usage, simply use the built-in file picker in the application.

---

## Running the app again later

Next time, you only need:

```bash
conda activate moldb
cd path\to\yourproject
python run.py
```

## 3. Run tests

```bash
pytest tests/
```

---

# Features

- Add / edit / delete molecules
- Search by:
  - Name (fuzzy)
  - CAS number
  - Exact SMILES
- Structure similarity search (Tanimoto)
- Substructure search via Kekule.js drawing widget
- 2D structure visualization (RDKit SVG rendering)
- Duplicate detection via InChIKey
- Fully offline operation
- Interactive API documentation

---

# Build Windows .exe

```bash
conda activate moldb
pip install pyinstaller

cd build
pyinstaller moldb.spec --clean

# Output:
# dist/MolDB.exe
```

---

# Project Structure

```text
project-root/
├── moldb/                  # Core library (importable)
├── ui/                     # FastAPI app + static frontend
├── tests/                  # Pytest suite
├── build/                  # PyInstaller spec + RDKit hooks
├── docs/
│   └── screenshots/
│       ├── banner.png
│       ├── molecule-browser.png
│       ├── molecule-detail.png
│       ├── structure-search.png
│       ├── molecule-editor.png
│       └── api-docs.png
├── run.py                  # Entrypoint
└── README.md
```

---

# API Docs

Run the application and visit:

http://localhost:8000/api/docs

---

# Tech Stack

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

---

# License

MIT License
