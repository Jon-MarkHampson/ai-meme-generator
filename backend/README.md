# ai-meme-generator

## Install dependencies

Use the following command

```bash
uv pip install pyproject.toml
```

## Running the app

Use the following command to start the development server from inside the backend folder:

```bash
uvicorn main:app --reload --app-dir .
```

## Deploying to Render

You can deploy both the FastAPI backend and the Next.js frontend using the root-level `render.yaml` blueprint.

Steps:

- Connect your GitHub repo to Render.
- Click **New → Blueprint** and select this repository.
- Render will detect `render.yaml` and create two Web Services:
  - `ai-meme-generator-backend` (Python/FastAPI)
  - `ai-meme-generator-frontend` (Node/Next.js)
- Populate the backend service environment variables (secrets live in this service or an Environment Group):
  - `DATABASE_URL` (Supabase Postgres connection)
  - `JWT_SECRET`, `JWT_ALGORITHM` (HS256), `ACCESS_TOKEN_EXPIRE_MINUTES`
  - `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `LOGFIRE_TOKEN`
  - `SUPABASE_URL`, `SUPABASE_PASSWORD`, `SUPABASE_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
  - `AI_IMAGE_BUCKET`
- Health check endpoint: `/health/`

Notes:

- `FRONTEND_URL` and `NEXT_PUBLIC_API_BASE_URL` are auto-populated via `fromService` references inside `render.yaml`. Override them if you need additional origins (e.g., localhost).
- Backend build uses `pip install -e .` against `pyproject.toml`; Python runtime is pinned with `runtime.txt`.
- Frontend build runs `npm install && npm run build`; start command is `npm run start` for Next.js.
- Both services bind to Render’s `$PORT`, and SSE streaming from `/generate/meme` works on Render Web Services.
