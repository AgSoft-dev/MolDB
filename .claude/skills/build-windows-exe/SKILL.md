---
name: build-windows-exe
description: Build and smoke-test the MolDB Windows executable with PyInstaller. Use when asked to build, package or release the exe, or after changing imports, static assets or build/moldb.spec.
---

1. Use a clean environment that has the project dependencies plus `pyinstaller` (on Windows: `conda activate moldb`).
2. Build:
   ```bash
   cd build && pyinstaller moldb.spec --clean
   ```
   The output is `dist/MolDB.exe` (relative to `build/`).
3. If you added an import, check the build log for `ModuleNotFoundError` and add it to `hiddenimports` (or `collect_submodules`) in `build/moldb.spec`. The RDKit binaries come from `build/hooks/hook-rdkit.py`.
4. Smoke test **with the network disabled**:
   - launch the exe and wait until the server answers;
   - `GET /` returns the UI with no mojibake; `GET /ketcher/index.html` and its `static/js/main.*.js` return 200 with a JavaScript content type;
   - create a DB, add a molecule (e.g. `CCO`), then run text, similarity and substructure searches;
   - close the app, then confirm the DB file still exists at the absolute path shown in the UI, outside `%TEMP%`, and that it can be deleted (no lingering lock).
5. Report the exe size, the build warnings, and the smoke-test results.
