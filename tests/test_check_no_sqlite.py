import sqlite3
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "check_no_sqlite", Path(__file__).resolve().parent.parent / "scripts" / "check_no_sqlite.py"
)
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)


def test_detects_sqlite_without_extension(tmp_path):
    db = tmp_path / "mydb"
    sqlite3.connect(db).execute("CREATE TABLE t (x)").connection.close()
    assert check.is_sqlite(str(db))
    assert check.main([str(db)]) == 1


def test_allows_regular_files(tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text("SQLite is great")
    assert not check.is_sqlite(str(f))
    assert check.main([str(f)]) == 0
