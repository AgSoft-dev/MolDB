import os
import sys
import pytest
from fastapi.testclient import TestClient

from moldb.paths import resolve_db_path, user_data_dir
import ui.app as app_module
from ui.app import app


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    d = tmp_path / "data"
    monkeypatch.setenv("MOLDB_DATA_DIR", str(d))
    yield d
    if app_module.db is not None:
        app_module.db.engine.dispose()
    app_module.db = app_module.search = None
    app_module.current_db_path = ""


def test_user_data_dir_created(data_dir):
    assert user_data_dir() == str(data_dir)
    assert data_dir.is_dir()


def test_relative_path_goes_to_data_dir(data_dir):
    assert resolve_db_path("lab.sqlite") == os.path.join(str(data_dir), "lab.sqlite")


def test_absolute_path_kept(tmp_path):
    p = str(tmp_path / "elsewhere" / "lab.sqlite")
    assert resolve_db_path(p) == p


def test_relative_path_not_next_to_code():
    code_dir = os.path.dirname(os.path.abspath(app_module.__file__))
    assert not resolve_db_path("lab.sqlite").startswith(code_dir)


def test_path_inside_frozen_bundle_rejected(tmp_path, monkeypatch):
    bundle = tmp_path / "_MEI12345"
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    with pytest.raises(ValueError):
        resolve_db_path(str(bundle / "ui" / "lab.sqlite"))
    # Paths outside the bundle are still fine
    assert resolve_db_path("lab.sqlite").endswith("lab.sqlite")


def test_api_create_relative_db_lands_in_data_dir(data_dir):
    client = TestClient(app)
    res = client.post("/api/db/path", json={"path": "molecules_2026-10-11.sqlite", "create": True})
    assert res.status_code == 200
    expected = os.path.join(str(data_dir), "molecules_2026-10-11.sqlite")
    assert res.json()["path"] == expected
    assert res.json()["data_dir"] == str(data_dir)
    assert os.path.exists(expected)


def test_api_rejects_path_inside_bundle(tmp_path, monkeypatch):
    bundle = tmp_path / "_MEI999"
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    client = TestClient(app)
    res = client.post("/api/db/path", json={"path": str(bundle / "x.sqlite"), "create": True})
    assert res.status_code == 422
    assert not (bundle / "x.sqlite").exists()
