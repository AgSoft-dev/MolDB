"""RDKit chemistry helpers. All functions raise InvalidSMILES on bad input."""
from __future__ import annotations
from .exceptions import InvalidSMILES

try:
    from rdkit import Chem
    from rdkit.Chem import Draw, Descriptors, rdMolDescriptors, DataStructs
    from rdkit.Chem import AllChem
    from rdkit.Chem.Draw import rdMolDraw2D
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False


def _mol(smiles: str):
    if not RDKIT_AVAILABLE:
        raise RuntimeError("RDKit not installed. See README for install instructions.")
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise InvalidSMILES(f"Invalid SMILES: {smiles!r}")
    return mol


def normalize_smiles(smiles: str) -> str:
    return Chem.MolToSmiles(_mol(smiles))


def smiles_to_inchikey(smiles: str) -> str:
    from rdkit.Chem.inchi import MolToInchiKey
    return MolToInchiKey(_mol(smiles))


def smiles_to_svg(smiles: str, size: tuple[int, int] = (300, 200)) -> str:
    mol = _mol(smiles)
    AllChem.Compute2DCoords(mol)
    drawer = rdMolDraw2D.MolDraw2DSVG(*size)
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    return drawer.GetDrawingText()


def smiles_to_fingerprint(smiles: str):
    return AllChem.GetMorganFingerprintAsBitVect(_mol(smiles), radius=2, nBits=2048)


def tanimoto(fp1, fp2) -> float:
    return DataStructs.TanimotoSimilarity(fp1, fp2)


def get_formula(smiles: str) -> str:
    return rdMolDescriptors.CalcMolFormula(_mol(smiles))


def get_mw(smiles: str) -> float:
    return round(Descriptors.MolWt(_mol(smiles)), 4)


def has_substructure(smiles: str, query_smiles: str) -> bool:
    return _mol(smiles).HasSubstructMatch(_mol(query_smiles))
