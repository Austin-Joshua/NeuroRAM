# Database Directory Guide

This folder contains all database-related storage and assets.

## Subfolders

- `migrations/` - schema migration scripts.
- `seed_data/` - sample/seed JSON payloads for local initialization.
- `exports/` - generated exports for reports or snapshots.

## Runtime files

- Primary SQLite database file: `neuroram.db`.
- SQLite WAL side files (`*.db-wal`, `*.db-shm`) are runtime artifacts and are gitignored.

## Storage policy

- Keep schema/migration/seed assets versioned.
- Keep runtime cache/artifact files untracked.
- Backend modules read/write this folder through settings in `neuroram/config/settings.py`.
