import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from moldb.database import MoleculeDB
from moldb.search import SearchEngine
from moldb.models import Molecule

import ui.app as app_module
from ui.app import app

ETHANOL_SMILES = "CCO"
BENZENE_SMILES = "c1ccccc1"


@pytest.fixture(autouse=True)
def fresh_db():
    """Point the app at a fresh temp database for every test."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        path = f.name
    db = MoleculeDB(path, create=True, migrate=True)
    app_module.db = db
    app_module.search = SearchEngine(db)
    app_module.current_db_path = path
    yield db
    os.unlink(path)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def ethanol(fresh_db):
    """Pre-insert an ethanol molecule and return it."""
    return fresh_db.add(Molecule(name="Ethanol", smiles=ETHANOL_SMILES))


# ── Update endpoint: derived fields ───────────────────────────────────────────

def test_update_smiles_regenerates_svg(client, ethanol):
    """Changing SMILES must produce a new svg_cache."""
    old_svg = ethanol.svg_cache
    res = client.put(f"/api/molecules/{ethanol.id}", json={"smiles": BENZENE_SMILES})
    assert res.status_code == 200
    new_svg = res.json()["svg_cache"]
    assert new_svg is not None
    assert new_svg != old_svg


def test_update_smiles_regenerates_inchikey(client, ethanol):
    res = client.put(f"/api/molecules/{ethanol.id}", json={"smiles": BENZENE_SMILES})
    assert res.status_code == 200
    assert res.json()["inchikey"] == "UHOVQNZJYSORNB-UHFFFAOYSA-N"


def test_update_smiles_regenerates_formula_and_mw(client, ethanol):
    res = client.put(f"/api/molecules/{ethanol.id}", json={"smiles": BENZENE_SMILES})
    assert res.status_code == 200
    data = res.json()
    assert data["molecular_formula"] == "C6H6"
    assert data["molecular_weight"] == pytest.approx(78.11, abs=0.1)


def test_update_invalid_smiles_returns_422(client, ethanol):
    res = client.put(f"/api/molecules/{ethanol.id}", json={"smiles": "not-a-smiles"})
    assert res.status_code == 422


def test_update_without_smiles_preserves_derived_fields(client, ethanol):
    """Updating name/notes only must not touch svg_cache or inchikey."""
    original_svg = ethanol.svg_cache
    original_inchikey = ethanol.inchikey
    res = client.put(f"/api/molecules/{ethanol.id}", json={"name": "Ethanol renamed", "notes": "just a note"})
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Ethanol renamed"
    assert data["svg_cache"] == original_svg
    assert data["inchikey"] == original_inchikey


def test_update_smiles_reflected_in_get(client, ethanol):
    """After PUT, a subsequent GET must return the updated svg_cache."""
    client.put(f"/api/molecules/{ethanol.id}", json={"smiles": BENZENE_SMILES})
    res = client.get(f"/api/molecules/{ethanol.id}")
    assert res.status_code == 200
    assert res.json()["svg_cache"] is not None
    assert "ethanol" not in res.json()["svg_cache"].lower()