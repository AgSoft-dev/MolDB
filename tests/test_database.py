import pytest
import os
import tempfile
from moldb.database import MoleculeDB
from moldb.models import Molecule, MoleculeUpdate
from moldb.exceptions import MoleculeNotFound, DuplicateMolecule


@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        path = f.name
    d = MoleculeDB(path, create=True, migrate=True)
    yield d
    os.unlink(path)


def test_add_and_get(db):
    mol = Molecule(name="Ethanol", smiles="CCO", inchikey="LFQSCWFLJHTTHZ-UHFFFAOYSA-N")
    saved = db.add(mol)
    assert saved.id is not None
    fetched = db.get(saved.id)
    assert fetched.name == "Ethanol"


def test_add_computes_inchikey_when_missing(db):
    mol = db.add(Molecule(name="Ethanol", smiles="CCO"))
    assert mol.id is not None
    assert mol.inchikey == "LFQSCWFLJHTTHZ-UHFFFAOYSA-N"


def test_add_duplicate_smiles_raises(db):
    db.add(Molecule(name="Benzene", smiles="c1ccccc1"))
    with pytest.raises(DuplicateMolecule):
        db.add(Molecule(name="Benzene copy", smiles="c1ccccc1"))


def test_update(db):
    mol = db.add(Molecule(name="Old Name", smiles="CCO"))
    updated = db.update(mol.id, MoleculeUpdate(name="New Name"))
    assert updated.name == "New Name"


def test_delete(db):
    mol = db.add(Molecule(name="Water", smiles="O"))
    db.delete(mol.id)
    with pytest.raises(MoleculeNotFound):
        db.get(mol.id)


def test_not_found(db):
    with pytest.raises(MoleculeNotFound):
        db.get(9999)


def test_duplicate_inchikey(db):
    db.add(Molecule(name="Benzene", smiles="c1ccccc1", inchikey="UHOVQNZJYSORNB-UHFFFAOYSA-N"))
    with pytest.raises(DuplicateMolecule):
        db.add(Molecule(name="Benzene copy", smiles="c1ccccc1", inchikey="UHOVQNZJYSORNB-UHFFFAOYSA-N"))


def test_list_all(db):
    db.add(Molecule(name="A", smiles="C"))
    db.add(Molecule(name="B", smiles="CC"))
    assert len(db.list_all()) == 2
