from __future__ import annotations
import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from typing import Optional

from moldb import MoleculeDB, SearchEngine, chem
from moldb.models import Molecule, MoleculeCreate, MoleculeRead, MoleculeUpdate
from moldb.exceptions import InvalidSMILES, DuplicateMolecule, MoleculeNotFound

DB_PATH = os.environ.get("MOLDB_PATH", "").strip()
db = None
search = None
current_db_path = ""
if DB_PATH:
    if not os.path.isabs(DB_PATH):
        DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_PATH)
    DB_PATH = os.path.normpath(DB_PATH)
    if os.path.exists(DB_PATH):
        db = MoleculeDB(DB_PATH)
        search = SearchEngine(db)
        current_db_path = DB_PATH

app = FastAPI(title="MolDB", version="0.1.0", docs_url="/api/docs")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Ketcher standalone build — place the unzipped release at ui/static/ketcher/
KETCHER_DIR = os.path.join(STATIC_DIR, "ketcher")
if os.path.isdir(KETCHER_DIR):
    app.mount("/ketcher", StaticFiles(directory=KETCHER_DIR, html=True), name="ketcher")


@app.get("/", response_class=HTMLResponse)
async def index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return f.read()


# ── Molecules CRUD ─────────────────────────────────────────────────────────────

class DBPathPayload(BaseModel):
    path: str
    create: Optional[bool] = False
    migrate: Optional[bool] = False


class DBPathResponse(BaseModel):
    path: str


def get_db_obj() -> MoleculeDB:
    if db is None:
        raise HTTPException(400, "No database loaded. Select an existing SQLite file or create one in advanced mode.")
    return db


def get_search_engine() -> SearchEngine:
    if search is None:
        raise HTTPException(400, "No database loaded. Select an existing SQLite file or create one in advanced mode.")
    return search


@app.get("/api/db/path", response_model=DBPathResponse)
async def get_db_path():
    return {"path": current_db_path}


@app.post("/api/db/path", response_model=DBPathResponse)
async def set_db_path(payload: DBPathPayload):
    if not payload.path.strip():
        raise HTTPException(422, "Database path must not be empty")
    path = payload.path.strip()
    # Ensure a recognised SQLite extension so callers can omit it.
    if not path.endswith(('.sqlite', '.db')):
        path += '.sqlite'
    # Resolve relative paths against the directory containing app.py,
    # not the process CWD (which may differ when launched via uvicorn/gunicorn).
    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    path = os.path.normpath(path)
    create = payload.create or False
    migrate = payload.migrate or False
    if not os.path.exists(path) and not create:
        raise HTTPException(404, "Database file does not exist. Use advanced mode to create a new database.")
    try:
        new_db = MoleculeDB(path, create=create, migrate=migrate)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))
    global db, search, current_db_path
    db = new_db
    search = SearchEngine(db)
    current_db_path = path
    return {"path": current_db_path}


class MigrationStatusResponse(BaseModel):
    pending: int


@app.get("/api/db/migrate", response_model=MigrationStatusResponse)
async def get_migration_status():
    pending = get_db_obj().needs_migration()
    return {"pending": pending}


@app.post("/api/db/migrate", response_model=MigrationStatusResponse)
async def apply_migration():
    pending = get_db_obj().apply_migrations()
    return {"pending": pending}


@app.post("/api/molecules", response_model=MoleculeRead, status_code=201)
async def create_molecule(payload: MoleculeCreate):
    try:
        canonical = chem.normalize_smiles(payload.smiles)
        inchikey  = chem.smiles_to_inchikey(canonical)
        svg       = chem.smiles_to_svg(canonical)
        formula   = chem.get_formula(canonical)
        mw        = chem.get_mw(canonical)
    except InvalidSMILES as e:
        raise HTTPException(422, str(e))

    mol = Molecule(
        name=payload.name,
        cas_number=payload.cas_number,
        project=payload.project,
        notes=payload.notes,
        smiles=canonical,
        inchikey=inchikey,
        svg_cache=svg,
        molecular_formula=formula,
        molecular_weight=mw,
    )
    try:
        return get_db_obj().add(mol)
    except DuplicateMolecule as e:
        raise HTTPException(409, str(e))


@app.get("/api/molecules", response_model=list[MoleculeRead])
async def list_molecules(limit: int = 100, offset: int = 0):
    return get_db_obj().list_all(limit=limit, offset=offset)


@app.get("/api/molecules/{mol_id}", response_model=MoleculeRead)
async def get_molecule(mol_id: int):
    try:
        return get_db_obj().get(mol_id)
    except MoleculeNotFound:
        raise HTTPException(404, f"Molecule {mol_id} not found")


@app.put("/api/molecules/{mol_id}", response_model=MoleculeRead)
async def update_molecule(mol_id: int, data: MoleculeUpdate):
    try:
        return get_db_obj().update(mol_id, data)
    except MoleculeNotFound:
        raise HTTPException(404, f"Molecule {mol_id} not found")


@app.delete("/api/molecules/{mol_id}", status_code=204)
async def delete_molecule(mol_id: int):
    try:
        get_db_obj().delete(mol_id)
    except MoleculeNotFound:
        raise HTTPException(404, f"Molecule {mol_id} not found")


# ── SVG ────────────────────────────────────────────────────────────────────────

@app.get("/api/molecules/{mol_id}/svg")
async def get_svg(mol_id: int):
    try:
        mol = get_db_obj().get(mol_id)
    except MoleculeNotFound:
        raise HTTPException(404)
    svg = mol.svg_cache or chem.smiles_to_svg(mol.smiles)
    return Response(content=svg, media_type="image/svg+xml")


# ── Search ─────────────────────────────────────────────────────────────────────

@app.get("/api/search", response_model=list[MoleculeRead])
async def search_molecules(
    q: Optional[str] = None,
):
    if q:
        return get_search_engine().by_all(q)
    raise HTTPException(400, "Provide q parameter")


class StructureQuery(BaseModel):
    smiles: str
    threshold: float = 0.7
    mode: str = "similarity"  # "similarity" | "substructure"


class SimilarityResult(BaseModel):
    molecule: MoleculeRead
    score: float


@app.post("/api/search/structure", response_model=list[SimilarityResult])
async def search_structure(body: StructureQuery):
    if body.mode == "substructure":
        hits = get_search_engine().by_substructure(body.smiles)
        return [SimilarityResult(molecule=MoleculeRead.from_orm(m), score=1.0) for m in hits]
    hits = get_search_engine().by_structure(body.smiles, threshold=body.threshold)
    return [SimilarityResult(molecule=MoleculeRead.from_orm(m), score=s) for m, s in hits]


# ── Chem utilities ─────────────────────────────────────────────────────────────

class NormalizeRequest(BaseModel):
    smiles: str


@app.post("/api/chem/normalize")
async def normalize(body: NormalizeRequest):
    try:
        canonical = chem.normalize_smiles(body.smiles)
        return {
            "canonical_smiles": canonical,
            "inchikey": chem.smiles_to_inchikey(canonical),
            "molecular_formula": chem.get_formula(canonical),
            "molecular_weight": chem.get_mw(canonical),
        }
    except InvalidSMILES as e:
        raise HTTPException(422, str(e))