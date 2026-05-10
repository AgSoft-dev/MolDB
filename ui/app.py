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

DB_PATH = os.environ.get("MOLDB_PATH", "moldb.sqlite")
db = MoleculeDB(DB_PATH)
search = SearchEngine(db)

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
        notes=payload.notes,
        smiles=canonical,
        inchikey=inchikey,
        svg_cache=svg,
        molecular_formula=formula,
        molecular_weight=mw,
    )
    try:
        return db.add(mol)
    except DuplicateMolecule as e:
        raise HTTPException(409, str(e))


@app.get("/api/molecules", response_model=list[MoleculeRead])
async def list_molecules(limit: int = 100, offset: int = 0):
    return db.list_all(limit=limit, offset=offset)


@app.get("/api/molecules/{mol_id}", response_model=MoleculeRead)
async def get_molecule(mol_id: int):
    try:
        return db.get(mol_id)
    except MoleculeNotFound:
        raise HTTPException(404, f"Molecule {mol_id} not found")


@app.put("/api/molecules/{mol_id}", response_model=MoleculeRead)
async def update_molecule(mol_id: int, data: MoleculeUpdate):
    try:
        return db.update(mol_id, data)
    except MoleculeNotFound:
        raise HTTPException(404, f"Molecule {mol_id} not found")


@app.delete("/api/molecules/{mol_id}", status_code=204)
async def delete_molecule(mol_id: int):
    try:
        db.delete(mol_id)
    except MoleculeNotFound:
        raise HTTPException(404, f"Molecule {mol_id} not found")


# ── SVG ────────────────────────────────────────────────────────────────────────

@app.get("/api/molecules/{mol_id}/svg")
async def get_svg(mol_id: int):
    try:
        mol = db.get(mol_id)
    except MoleculeNotFound:
        raise HTTPException(404)
    svg = mol.svg_cache or chem.smiles_to_svg(mol.smiles)
    return Response(content=svg, media_type="image/svg+xml")


# ── Search ─────────────────────────────────────────────────────────────────────

@app.get("/api/search", response_model=list[MoleculeRead])
async def search_molecules(
    q: Optional[str] = None,
    cas: Optional[str] = None,
    smiles: Optional[str] = None,
):
    if q:
        return search.by_name(q)
    if cas:
        result = search.by_cas(cas)
        return [result] if result else []
    if smiles:
        result = search.by_smiles_exact(smiles)
        return [result] if result else []
    raise HTTPException(400, "Provide q, cas, or smiles parameter")


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
        hits = search.by_substructure(body.smiles)
        return [SimilarityResult(molecule=m, score=1.0) for m in hits]
    hits = search.by_structure(body.smiles, threshold=body.threshold)
    return [SimilarityResult(molecule=m, score=s) for m, s in hits]


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