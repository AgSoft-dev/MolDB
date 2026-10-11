---
name: security-checklist
description: Pre-PR checklist for MolDB covering security, offline and Windows checks. Use before committing or opening a PR that touches ui/, moldb/, run.py or build/.
---

Run through these checks on the current change and fix or report each failure.

1. **No DB files staged**:
   ```bash
   git diff --cached --name-only -z | xargs -0 -I{} sh -c 'head -c 15 "{}" 2>/dev/null | grep -q "SQLite format" && echo "DB FILE: {}"'
   ```
2. **No external URLs in served assets** (offline): `grep -rnE "https?://" ui/static --include=*.html --include=*.js --include=*.css | grep -v ketcher | grep -v w3.org`
3. **Escaping**: every `${...}` interpolation in `ui/static/app.js` that is inserted as HTML goes through `escHtml`, or the code uses `textContent` or DOM APIs. Never put DB values in inline `onclick` strings.
4. **API input**: new request models use `Field` bounds (`max_length`, `ge`/`le`) and `Literal` for enums. Derived fields are never client-writable.
5. **Errors**: no `HTTPException(..., str(e))` and no absolute paths in responses.
6. **Windows**: `open(` calls pass `encoding="utf-8"`. No path resolution against `__file__` for user data. Engines are disposed. New third-party imports are collected by `build/moldb.spec`.
7. **Tests**: `pytest tests/` passes, and new behavior has a test.

Then run the `moldb-security-reviewer` agent on the diff for a second look.
