import pytest
from moldb.chem import normalize_smiles, smiles_to_inchikey, get_formula, get_mw
from moldb.exceptions import InvalidSMILES


def test_normalize_benzene():
    assert normalize_smiles("c1ccccc1") == "c1ccccc1"


def test_normalize_ethanol():
    # different input forms should canonicalize
    assert normalize_smiles("OCC") == normalize_smiles("CCO")


def test_inchikey_benzene():
    key = smiles_to_inchikey("c1ccccc1")
    assert key.startswith("UHOVQNZJYSORNB")


def test_formula_ethanol():
    assert get_formula("CCO") == "C2H6O"


def test_mw_ethanol():
    assert 46.0 < get_mw("CCO") < 46.1


def test_invalid_smiles():
    with pytest.raises(InvalidSMILES):
        normalize_smiles("not_a_smiles!!!")
