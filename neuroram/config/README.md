# NeuroRAM Config

Configuration ownership for the entire platform lives here.

## Files

- `config.py` - runtime config object (`CONFIG`)
- `settings.py` - constants, directories, defaults, and `.env` loading

## Responsibility

- Define environment-driven thresholds and intervals.
- Define canonical paths for DB, exports, models, and assets.
- Keep parsing/default logic centralized to avoid hardcoded values in app modules.
