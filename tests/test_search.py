import pytest
import os
import tempfile
from moldb.database import MoleculeDB
from moldb.search import SearchEngine
from moldb.models import Molecule


@pytest.fixture
def populated_db():
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        path = f.name
    db = MoleculeDB(path, create=True, migrate=True)
    db.add(Molecule(name="Aspirin", smiles="CC(=O)Oc1ccccc1C(=O)O", cas_number="50-78-2"))
    db.add(Molecule(name="Caffeine", smiles="Cn1cnc2c1c(=O)n(c(=O)n2C)C", cas_number="58-08-2"))
    db.add(Molecule(name="Benzene", smiles="c1ccccc1", cas_number="71-43-2"))
    yield db
    os.unlink(path)


def test_by_name_exact(populated_db):
    se = SearchEngine(populated_db)
    results = se.by_name("Aspirin", fuzzy=False)
    assert any(m.name == "Aspirin" for m in results)


def test_by_name_fuzzy(populated_db):
    se = SearchEngine(populated_db)
    results = se.by_name("asprin")  # intentional typo
    assert any(m.name == "Aspirin" for m in results)


def test_by_cas(populated_db):
    se = SearchEngine(populated_db)
    mol = se.by_cas("58-08-2")
    assert mol is not None
    assert mol.name == "Caffeine"


def test_by_cas_not_found(populated_db):
    se = SearchEngine(populated_db)
    assert se.by_cas("00-00-0") is None


def test_by_smiles_exact(populated_db):
    se = SearchEngine(populated_db)
    mol = se.by_smiles_exact("c1ccccc1")
    assert mol is not None
    assert mol.name == "Benzene"


def test_by_smiles_exact_normalizes_stored_smiles(populated_db):
    populated_db.add(Molecule(name="Ethanol", smiles="OCC"))
    se = SearchEngine(populated_db)
    mol = se.by_smiles_exact("CCO")
    assert mol is not None
    assert mol.name == "Ethanol"


def test_by_all_searches_project(populated_db):
    populated_db.add(Molecule(name="API Molecule", smiles="CCO", project="API Screening"))
    se = SearchEngine(populated_db)
    results = se.by_all("api")
    assert any(m.project == "API Screening" for m in results)


def test_by_all_searches_notes(populated_db):
    populated_db.add(Molecule(name="Note Test", smiles="CCO", notes="special chemistry notes"))
    se = SearchEngine(populated_db)
    results = se.by_all("chemistry")
    assert any(m.notes == "special chemistry notes" for m in results)
