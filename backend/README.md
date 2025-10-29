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
- After Render creates both services, add the required secrets via each service → Settings → Environment:
  - **Backend secrets**: `JWT_SECRET`, `AI_SERVICE_API_KEY`, `DATABASE_URL`
  - **Frontend secrets**: (none required beyond what's in render.yaml)

### Backend Configuration

The backend service is configured with:

- Runtime: Python (starter plan)
- Root directory: `backend`
- Health check: `/health/`
- Build: `pip install -U pip && pip install -e .`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT --app-dir .`

Environment variables (predefined in render.yaml):

- `ENVIRONMENT`: production
- `LOG_LEVEL`: info
- `JWT_ALGORITHM`: HS256
- `ACCESS_TOKEN_EXPIRE_MINUTES`: 5
- `AI_IMAGE_BUCKET`: memes
- `FRONTEND_URL`: <https://ai-meme-generator-frontend.onrender.com>

### Frontend Configuration

The frontend service is configured with:

- Runtime: Node (starter plan)
- Root directory: `frontend`
- Build: `npm install && npm run build`
- Start: `npm run start`

Environment variables (predefined in render.yaml):

- `NODE_ENV`: production
- `NEXT_PUBLIC_API_URL`: <https://ai-meme-generator-backend.onrender.com>

### Notes

- Only non-secret defaults are defined in `render.yaml`. Secrets must be added manually in the Render dashboard to keep them out of git.
- Both services automatically bind to Render's `$PORT`.
- SSE streaming from `/generate/meme` works on Render Web Services.
