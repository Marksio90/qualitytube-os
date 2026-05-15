# QualityTube OS

Monorepo scaffold containing:

- `backend/` FastAPI backend and tests
- `frontend/` React + Vite frontend
- `docs/` project documentation

## Backend

- Run API: `uvicorn app.main:app --reload --app-dir backend`
- Run tests: `pytest`
- Lint: `ruff check backend`

## Frontend

- Install: `npm install`
- Run dev server: `npm run dev --prefix frontend`
