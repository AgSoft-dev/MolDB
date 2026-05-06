class MolDBError(Exception):
    pass

class InvalidSMILES(MolDBError):
    pass

class DuplicateMolecule(MolDBError):
    pass

class MoleculeNotFound(MolDBError):
    pass
