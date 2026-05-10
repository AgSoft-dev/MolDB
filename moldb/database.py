from __future__ import annotations
from sqlmodel import SQLModel, Session, create_engine, select
from sqlalchemy import text
from .models import Molecule, MoleculeUpdate
from .exceptions import MoleculeNotFound, DuplicateMolecule


class MoleculeDB:
    def __init__(self, db_path: str = "moldb.sqlite"):
        self.db_path = db_path
        url = f"sqlite:///{db_path}"
        self.engine = create_engine(url, connect_args={"check_same_thread": False})
        SQLModel.metadata.create_all(self.engine)
        self._ensure_project_column_exists()

    def _ensure_project_column_exists(self) -> None:
        with self.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info('molecule')"))
            columns = [row[1] for row in result.fetchall()]
            if 'project' not in columns:
                conn.execute(text("ALTER TABLE molecule ADD COLUMN project TEXT"))
                conn.commit()

    def add(self, mol: Molecule) -> Molecule:
        with Session(self.engine) as s:
            if mol.inchikey:
                existing = s.exec(
                    select(Molecule).where(Molecule.inchikey == mol.inchikey)
                ).first()
                if existing:
                    raise DuplicateMolecule(
                        f"Molecule with InChIKey {mol.inchikey} already exists (id={existing.id})"
                    )
            s.add(mol)
            s.commit()
            s.refresh(mol)
            return mol

    def get(self, mol_id: int) -> Molecule:
        with Session(self.engine) as s:
            mol = s.get(Molecule, mol_id)
            if mol is None:
                raise MoleculeNotFound(mol_id)
            return mol

    def update(self, mol_id: int, data: MoleculeUpdate) -> Molecule:
        with Session(self.engine) as s:
            mol = s.get(Molecule, mol_id)
            if mol is None:
                raise MoleculeNotFound(mol_id)
            for field, val in data.dict(exclude_unset=True).items():
                setattr(mol, field, val)
            s.add(mol)
            s.commit()
            s.refresh(mol)
            return mol

    def delete(self, mol_id: int) -> bool:
        with Session(self.engine) as s:
            mol = s.get(Molecule, mol_id)
            if mol is None:
                raise MoleculeNotFound(mol_id)
            s.delete(mol)
            s.commit()
            return True

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Molecule]:
        with Session(self.engine) as s:
            return list(s.exec(select(Molecule).offset(offset).limit(limit)).all())

    def count(self) -> int:
        with Session(self.engine) as s:
            return len(s.exec(select(Molecule)).all())
