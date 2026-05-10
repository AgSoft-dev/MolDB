from typing import Optional
from sqlmodel import SQLModel, Field


class MoleculeBase(SQLModel):
    name: str
    cas_number: Optional[str] = None
    smiles: str
    inchikey: Optional[str] = None
    molecular_formula: Optional[str] = None
    molecular_weight: Optional[float] = None
    project: Optional[str] = None
    notes: Optional[str] = None


class Molecule(MoleculeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    svg_cache: Optional[str] = None


class MoleculeCreate(MoleculeBase):
    pass


class MoleculeRead(MoleculeBase):
    id: int
    svg_cache: Optional[str] = None

    class Config:
        from_attributes = True


class MoleculeUpdate(SQLModel):
    name: Optional[str] = None
    cas_number: Optional[str] = None
    smiles: Optional[str] = None
    project: Optional[str] = None
    notes: Optional[str] = None
