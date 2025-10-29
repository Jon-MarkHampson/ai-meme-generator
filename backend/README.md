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

You can deploy the FastAPI backend to Render using the included `render.yaml` blueprint at the repo root.

Steps:

- Connect your GitHub repo to Render.
- Click New → Blueprint and select this repository.
- Render will detect `render.yaml` and create a Web Service for the backend.
- Set required environment variables in the service settings:
  - `DATABASE_URL` (Render PostgreSQL or Supabase Postgres URL)
  - `JWT_SECRET`, `JWT_ALGORITHM` (HS256), `ACCESS_TOKEN_EXPIRE_MINUTES`
  - `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `LOGFIRE_TOKEN`
  - `SUPABASE_URL`, `SUPABASE_PASSWORD`, `SUPABASE_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
  - `AI_IMAGE_BUCKET`
  - `FRONTEND_URL` (your Vercel domain for CORS)
- Health check endpoint: `/health/`

Notes:

- The service uses `pip install -e .` to install dependencies from `pyproject.toml`.
- Start command binds to `$PORT` as required by Render.
- Server-Sent Events streaming in `/generate/meme` is supported on Render web services.
