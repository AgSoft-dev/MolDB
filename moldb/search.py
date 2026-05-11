from __future__ import annotations
from .database import MoleculeDB
from .models import Molecule
from . import chem

try:
    from rapidfuzz import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False


class SearchEngine:
    def __init__(self, db: MoleculeDB):
        self.db = db

    def by_name(self, query: str, fuzzy: bool = True, limit: int = 20) -> list[Molecule]:
        all_mols = self.db.list_all(limit=10_000)
        if not fuzzy:
            q = query.lower()
            return [m for m in all_mols if q in m.name.lower()][:limit]
        if FUZZY_AVAILABLE:
            names = {m.name: m for m in all_mols}
            hits = process.extract(query, names.keys(), scorer=fuzz.WRatio, limit=limit, score_cutoff=50)
            return [names[name] for name, _, _ in hits]
        q = query.lower()
        return [m for m in all_mols if q in m.name.lower()][:limit]

    def by_cas(self, cas: str) -> Molecule | None:
        all_mols = self.db.list_all(limit=10_000)
        return next((m for m in all_mols if m.cas_number == cas.strip()), None)

    def by_smiles_exact(self, smiles: str) -> Molecule | None:
        try:
            canonical_query = chem.normalize_smiles(smiles)
            query_inchikey = chem.smiles_to_inchikey(canonical_query)
        except Exception:
            return None

        all_mols = self.db.list_all(limit=10_000)
        for m in all_mols:
            if m.inchikey and m.inchikey == query_inchikey:
                return m
            if not m.smiles:
                continue
            try:
                if chem.normalize_smiles(m.smiles).lower() == canonical_query.lower():
                    return m
            except Exception:
                continue
        return None

    def by_structure(
        self, query_smiles: str, threshold: float = 0.7, limit: int = 20
    ) -> list[tuple[Molecule, float]]:
        try:
            qfp = chem.smiles_to_fingerprint(query_smiles)
        except Exception:
            return []
        results: list[tuple[Molecule, float]] = []
        for mol in self.db.list_all(limit=10_000):
            if not mol.smiles:
                continue
            try:
                mfp = chem.smiles_to_fingerprint(mol.smiles)
                score = chem.tanimoto(qfp, mfp)
                if score >= threshold:
                    results.append((mol, score))
            except Exception:
                continue
        return sorted(results, key=lambda x: -x[1])[:limit]

    def by_substructure(self, query_smiles: str, limit: int = 20) -> list[Molecule]:
        results: list[Molecule] = []
        for mol in self.db.list_all(limit=10_000):
            if not mol.smiles:
                continue
            try:
                if chem.has_substructure(mol.smiles, query_smiles):
                    results.append(mol)
            except Exception:
                continue
        return results[:limit]

    def by_all(self, query: str, limit: int = 100) -> list[Molecule]:
        all_mols = self.db.list_all(limit=100_000)
        q_lower = query.lower()
        results = []
        for m in all_mols:
            if (q_lower in m.name.lower() or
                (m.cas_number and q_lower in m.cas_number.lower()) or
                (m.smiles and q_lower in m.smiles.lower()) or
                (m.project and q_lower in m.project.lower()) or
                (m.notes and q_lower in m.notes.lower())):
                results.append(m)
        return results[:limit]

