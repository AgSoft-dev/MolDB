---
name: db-migration
description: Add a safe SQLite schema change to MolDB. Use whenever a change adds, renames or removes a column, index or table in moldb/models.py or moldb/database.py.
---

User databases are confidential and often irreplaceable. A schema change must never lose data or touch files that are not MolDB databases.

1. Change the model in `moldb/models.py`.
2. Add the migration in `moldb/database.py`. It must be:
   - **idempotent**: check the current state (`PRAGMA table_info`, `PRAGMA index_list`) before acting;
   - **transactional**: run inside one transaction;
   - **preceded by a backup**: `sqlite3` online backup API to `<db>.bak-<timestamp>` before any `ALTER`;
   - **detectable**: report it in `needs_migration()` so the UI can offer it. Never apply it silently on open.
   Once versioned migrations exist (#16), bump `PRAGMA user_version` instead of ad-hoc checks.
3. For a new unique constraint, first query for existing duplicates and report them rather than failing mid-migration.
4. Add tests: migrate a fixture DB that has the old schema and assert data is preserved; run the migration twice and assert it is a no-op the second time.
5. Mention the migration in the PR description and the release notes.
