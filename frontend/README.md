# NeuroRAM Web UI

React + TypeScript + Vite frontend for the NeuroRAM memory intelligence platform.

## Purpose

This app consumes `GET /api/dashboard` from the FastAPI backend and renders:

- Dashboard KPIs and previews
- Memory and stability views
- Device intelligence cards and timeline
- Analysis with actionable recommendations
- Historical DB logs with filtering

## Run locally

```bash
npm install
npm run dev
```

By default, Vite runs on `http://localhost:5173`.

## Build and quality

```bash
npm run lint
npm run build
npx tsc -b
```

## Key folders

- `src/components/layout` - app shell (header/sidebar)
- `src/components/cards` - KPI cards
- `src/components/charts` - Recharts visualizations
- `src/components/tables` - reusable data table rendering
- `src/pages` - route pages
- `src/hooks/useDashboard.ts` - polling and API state
- `src/services/api.ts` - payload contracts and API calls

## API contract

This UI expects a structured payload with:

- `metrics`
- `devices`
- `trends`
- `analysis`
- `recommendations`

See `../docs/API_DOCS.md`.
