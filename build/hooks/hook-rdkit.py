"""
PyInstaller hook for RDKit.
Collects all native shared libraries and data files bundled with rdkit.
"""
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

datas    = collect_data_files('rdkit')
binaries = collect_dynamic_libs('rdkit')
