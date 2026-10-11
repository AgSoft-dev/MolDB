"""Filesystem locations for user data.

User databases must never be resolved against the package directory: in a
PyInstaller onefile build that lives in a temporary extraction folder
(sys._MEIPASS) which is deleted when the process exits.
"""
from __future__ import annotations
import os
import sys

APP_NAME = "MolDB"


def user_data_dir() -> str:
    """Per-user directory for databases. Created if missing.

    Override with the MOLDB_DATA_DIR environment variable.
    """
    override = os.environ.get("MOLDB_DATA_DIR", "").strip()
    if override:
        base = os.path.expanduser(override)
    elif sys.platform == "win32":
        root = os.environ.get("LOCALAPPDATA") or os.path.expanduser(r"~\AppData\Local")
        base = os.path.join(root, APP_NAME)
    elif sys.platform == "darwin":
        base = os.path.expanduser(f"~/Library/Application Support/{APP_NAME}")
    else:
        root = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        base = os.path.join(root, APP_NAME.lower())
    base = os.path.abspath(base)
    os.makedirs(base, exist_ok=True)
    return base


def _is_within(path: str, parent: str) -> bool:
    path, parent = os.path.normcase(path), os.path.normcase(parent)
    try:
        return os.path.commonpath([path, parent]) == parent
    except ValueError:  # different drives on Windows
        return False


def resolve_db_path(path: str) -> str:
    """Return an absolute, normalized path for a user-supplied DB path.

    Relative paths are resolved against user_data_dir(). Raises ValueError for
    paths inside the PyInstaller extraction folder, which is deleted on exit.
    """
    path = os.path.expanduser(path.strip())
    if not os.path.isabs(path):
        path = os.path.join(user_data_dir(), path)
    path = os.path.abspath(path)
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir and _is_within(path, os.path.abspath(bundle_dir)):
        raise ValueError("Databases cannot be stored inside the application's temporary folder.")
    return path
