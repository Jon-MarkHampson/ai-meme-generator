# AI Meme Generator — Multi‑Agent, Full‑Stack, Production‑Deployed

![Project Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)
![AI Meme Generator](https://img.shields.io/badge/AI-Meme%20Generator-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-15.3-000000?style=for-the-badge&logo=next.js&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white)

**A production-ready app that generates captioned memes using a manager–worker multi‑agent system and real‑time streaming. Deployed on Render; storage and CDN via Supabase.**

[Live Demo](https://ai-meme-generator-frontend.onrender.com) • [API Docs](https://ai-meme-generator-backend.onrender.com/docs) • [Report Bug](https://github.com/Jon-MarkHampson/ai-meme-generator/issues) • [Request Feature](https://github.com/Jon-MarkHampson/ai-meme-generator/issues)

---

## TL;DR

- **What it is:** Full‑stack application demonstrating **context-aware LLM workflows** with multi‑agent orchestration, real‑time streaming, and multi‑provider failover (OpenAI, Anthropic, Gemini).
- **Why it matters:** End‑to‑end product—from prompt engineering and evaluation frameworks to production deployment with monitoring. Shows system design thinking for creator-focused tools.
- **My role:** Solo developer spanning backend (Python/FastAPI), frontend (TypeScript/Next.js), infrastructure (Render, Supabase), and observability (Logfire). Full feature lifecycle from concept through launch.
- **Run now:** `docker compose up` **or** copy‑paste quickstart below (≤5 minutes).

> Short video demo recommended: add `/docs/demo.mp4` and link it here.

---

## Table of Contents

- [AI Meme Generator — Multi‑Agent, Full‑Stack, Production‑Deployed](#ai-meme-generator--multiagent-fullstack-productiondeployed)
  - [TL;DR](#tldr)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
    - [Highlights](#highlights)
  - [Tech Stack](#tech-stack)
    - [Backend](#backend)
    - [Frontend](#frontend)
    - [Infrastructure](#infrastructure)
  - [Architecture](#architecture)
    - [Model Configuration (`models-config.json`)](#model-configuration-models-configjson)
  - [Features](#features)
  - [Quickstart](#quickstart)
    - [Prerequisites](#prerequisites)
    - [Backend (FastAPI)](#backend-fastapi)
      - [Alternative: Using pip instead of uv](#alternative-using-pip-instead-of-uv)
    - [Frontend (Nextjs)](#frontend-nextjs)
  - [Environment Variables](#environment-variables)
    - [Backend (`.env`)](#backend-env)
    - [Frontend (`.env.local`)](#frontend-envlocal)
  - [API Documentation](#api-documentation)
    - [Interactive API Docs](#interactive-api-docs)
    - [Key Endpoints](#key-endpoints)
      - [Authentication](#authentication)
      - [Meme Generation](#meme-generation)
      - [User Gallery](#user-gallery)
      - [Conversations](#conversations)
  - [Deployment](#deployment)
    - [Render (Production)](#render-production)
    - [Docker (Local/Alt)](#docker-localalt)
      - [Backend Dockerfile](#backend-dockerfile)
      - [Frontend Dockerfile](#frontend-dockerfile)
      - [docker-compose.yml](#docker-composeyml)
  - [Project Structure](#project-structure)
    - [Backend Structure](#backend-structure)
    - [Frontend Structure](#frontend-structure)
  - [Contributing](#contributing)
  - [Learning Notes](#learning-notes)
  - [License](#license)
  - [Contact](#contact)
  - [Acknowledgements](#acknowledgements)

---

## Overview

AI Meme Generator demonstrates **production LLM workflows** using a manager–worker agent pattern. The system interprets prompts, generates contextually appropriate captions, produces images with text overlays, and streams progress to users via **Server‑Sent Events (SSE)**. Built with **OpenAI GPT‑4.1**, **Anthropic Claude 3.5**, and **Google Gemini** with automatic failover for reliability.

### Highlights

- Real‑time feedback (SSE) while generating
- Conversation persistence and summaries
- User gallery with favourites and deletion
- JWT auth with HTTP‑only cookies
- Production deployment on Render, storage/CDN via Supabase

<!-- Add screenshots/GIFs in /docs and reference relatively so they render on GitHub -->
<!-- ![Main Interface](docs/images/main-interface.png) -->

---

## Tech Stack

### Backend

| Technology | Purpose | Version |
|-----------|---------|---------|
| **FastAPI** | Async web framework | 0.115.12+ |
| **Python** | Core language | 3.12+ |
| **Pydantic AI** | Agent orchestration | 0.2.16+ |
| **SQLModel** | ORM with type safety | 0.0.24 |
| **PostgreSQL** | Database | Latest |
| **Supabase** | DB + Storage | 2.15.2+ |
| **OpenAI / Anthropic / Gemini SDKs** | LLMs + Images | Current |
| **Logfire** | Observability | 3.19.0+ |

### Frontend

| Technology | Purpose | Version |
|-----------|---------|---------|
| **Next.js** | App Router | 15.3.3 |
| **TypeScript** | Types | 5.0+ |
| **React** | UI | 19.0.0 |
| **Tailwind CSS** | Styling | 4.1.8 |
| **Radix UI** | A11y primitives | Latest |
| **Axios, RHF, Zod** | HTTP, forms, schemas | Latest |

### Infrastructure

- **Hosting:** Render (frontend + backend)
- **Database & Storage:** Supabase (PostgreSQL + Storage, CDN)
- **CI/CD:** Git‑based auto‑deployments
- **Monitoring:** Logfire

---

## Architecture

```bash
CLIENT (Next.js/TS)
  ↕  HTTPS / SSE
BACKEND (FastAPI)
  ├─ Manager Agent (GPT‑4.1/Claude) — intent parsing, orchestration, streaming
  ├─ Theme Agent — caption generation
  ├─ Image Agent (OpenAI/Gemini) — image + text overlay
  └─ Modify Agent — natural‑language edits
Core Services: Auth (JWT), Conversations, Image Storage, User Profiles
Data: Supabase Postgres (users, conversations, messages, meme records) + Storage (images)
```

**Feature‑based backend** with controller → service → model layers per feature (auth, generate, conversations, messages, user_memes, image_storage, llm_providers).

### Model Configuration (`models-config.json`)

Centralized **single source of truth** for all AI model definitions, shared across frontend and backend:

- Model metadata (name, description, capabilities, pricing, speed)
- Provider mapping (OpenAI, Anthropic, Gemini)
- Runtime configuration (enabled/disabled, default model)
- Makes adding new models trivial—update one file, both services sync automatically

---

## Features

- **Context‑Aware Generation:** Multi‑turn conversations with persistent history enable refinement and iteration
- **Real‑Time Streaming:** SSE with < 200ms response initiation for immediate user feedback
- **Prompt Engineering:** Natural‑language requests interpreted through structured agent workflows
- **Multi‑Provider Integration:** Runtime model selection (OpenAI, Anthropic, Gemini) with automatic failover
- **Image Modification:** Natural‑language edits ("make text bigger", "change background") on generated memes
- **Gallery & History:** Personal collection with favourites, conversation context linkage
- **Production‑Ready Auth:** JWT with HTTP‑only cookies, token refresh, protected routes

---

## Quickstart

### Prerequisites

- **Backend:** Python 3.12+, [`uv`](https://docs.astral.sh/uv/) (or `pip`), PostgreSQL (or Supabase)
- **Frontend:** Node.js 18+
- API keys for OpenAI, Anthropic, Gemini; Supabase project for DB + Storage

### Backend (FastAPI)

```bash
# 1) Clone repo and enter backend
git clone https://github.com/Jon-MarkHampson/ai-meme-generator.git \
  && cd ai-meme-generator/backend

# 2) Install deps (uv is fastest)
uv sync

# 3) Configure environment
cp .env.example .env  # fill required values

# 4) Run dev server
uv run uvicorn main:app --reload --app-dir .
# API → http://localhost:8000  •  Docs → http://localhost:8000/docs
```

#### Alternative: Using pip instead of uv

```bash
# 1) Clone repo and enter backend
git clone https://github.com/Jon-MarkHampson/ai-meme-generator.git \
  && cd ai-meme-generator/backend

# 2) Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3) Install dependencies
pip install -U pip
pip install -e .

# 4) Configure environment
cp .env.example .env  # fill required values

# 5) Run dev server
uvicorn main:app --reload --app-dir .
# API → http://localhost:8000  •  Docs → http://localhost:8000/docs
```

### Frontend (Nextjs)

```bash
# 1) Enter frontend
cd ../frontend

# 2) Install deps
npm install

# 3) Configure env
cp .env.example .env.local  # set NEXT_PUBLIC_API_BASE_URL to your backend URL

# 4) Run dev server
npm run dev
# App → http://localhost:3000
```

> **One‑liner (Docker)**: see `Deployment` for Dockerfiles/Compose, or run `docker compose up --build` if you’ve set them up locally.

---

## Environment Variables

### Backend (`.env`)

```bash
# Environment
ENVIRONMENT=development
LOG_LEVEL=info

# JWT
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=5

# Database
DATABASE_URL=postgresql://user:password@host:5432/database

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PASSWORD=your-db-password
SUPABASE_API_KEY=your-anon-key
# ⚠️ Service role keys grant elevated privileges. DO NOT expose in the frontend or commit to VCS.
# Provide via deployment secret store only if your backend requires admin operations.
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...

# Storage
AI_IMAGE_BUCKET=memes

# Observability (Optional)
LOGFIRE_TOKEN=your-logfire-token

# CORS
FRONTEND_URL=http://localhost:3000
```

### Frontend (`.env.local`)

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NODE_ENV=development
```

> **Security note:** Never expose secrets beginning with `sk-` or service‑role keys in the frontend or in the repo.

---

## API Documentation

### Interactive API Docs

The backend provides auto-generated interactive API documentation:

- **Swagger UI**: [https://ai-meme-generator-backend.onrender.com/docs](https://ai-meme-generator-backend.onrender.com/docs)
- **ReDoc**: [https://ai-meme-generator-backend.onrender.com/redoc](https://ai-meme-generator-backend.onrender.com/redoc)

### Key Endpoints

#### Authentication

```http
POST /auth/signup          # Register new user
POST /auth/login           # Authenticate user
POST /auth/logout          # End session
POST /auth/refresh         # Extend session
GET  /auth/session/status  # Check session validity
```

#### Meme Generation

```http
POST /generate/meme    # streams progress via SSE
```

#### User Gallery

```http
GET    /user-memes/           # List user's generated memes
GET    /user-memes/{id}       # Get single meme details
PATCH  /user-memes/{id}       # Update meme (e.g., favorite)
DELETE /user-memes/{id}       # Delete meme from gallery
```

#### Conversations

```http
GET    /conversations/        # List user's conversations
POST   /conversations/        # Create new conversation
GET    /conversations/{id}    # Get conversation details
PATCH  /conversations/{id}    # Update conversation summary
DELETE /conversations/{id}    # Delete conversation and messages
```

---

## Deployment

### Render (Production)

- Repo is configured with `render.yaml` for one‑click provisioning of frontend + backend.
- Set required environment variables in Render dashboards (keep secrets out of the repo).
- Health‑check: `https://ai-meme-generator-backend.onrender.com/health/`
- Push to `main` → auto‑redeploy both services.

### Docker (Local/Alt)

See example Dockerfiles/Compose below (adapt to your environment):

#### Backend Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY backend/pyproject.toml .
RUN pip install -e .
COPY backend/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY frontend/package*.json .
RUN npm ci
COPY frontend/ .
RUN npm run build
CMD ["npm", "start"]
```

#### docker-compose.yml

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://backend:8000
```

---

## Project Structure

### Backend Structure

```bash
backend/
├─ features/               # Feature modules (controller/service/model layers)
│  ├─ auth/                # JWT authentication & authorization
│  ├─ generate/            # AI meme generation (multi-agent core)
│  ├─ conversations/       # Conversation history management
│  ├─ messages/            # Message persistence & retrieval
│  ├─ user_memes/          # User gallery & meme CRUD
│  ├─ image_storage/       # Supabase storage integration
│  └─ llm_providers/       # Multi-provider LLM abstraction
├─ database/               # Connection pooling & session management
├─ utils/                  # Shared utilities (security, helpers)
├─ config.py               # Settings & environment variables
├─ models_registry.py      # Centralized model registration
├─ logging_config.py       # Structured logging configuration
├─ main.py                 # FastAPI application entry point
├─ api.py                  # Router registration
└─ pyproject.toml          # Dependencies & package metadata
```

### Frontend Structure

```bash
frontend/
├─ src/
│  ├─ app/                 # Next.js App Router pages & layouts
│  ├─ components/          # UI components (shadcn/ui, Radix, custom)
│  ├─ contexts/            # React context providers (Auth, etc.)
│  ├─ services/            # API client & HTTP modules
│  ├─ hooks/               # Custom React hooks
│  ├─ types/               # TypeScript type definitions
│  ├─ utils/               # Helper functions & utilities
│  └─ config/              # App configuration & constants
├─ public/                 # Static assets
└─ package.json            # Dependencies & scripts
```

---

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the repository**

   ```bash
   git clone https://github.com/your-username/ai-meme-generator.git
   ```

2. **Create a feature branch**

   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make your changes**
   - Follow existing code style
   - Add tests if applicable
   - Update documentation

4. **Commit your changes**

   ```bash
   git commit -m "Add amazing feature"
   ```

5. **Push to the branch**

   ```bash
   git push origin feature/amazing-feature
   ```

6. **Open a Pull Request**

   - Describe your changes
   - Link related issues
   - Request review

---

## Learning Notes

- Designed **evaluation frameworks** for measuring agent performance and model suitability across providers
- Built **resilient multi‑agent orchestration** with runtime provider selection and automatic failover
- Implemented **SSE streaming** with < 200ms response initiation, handling client back‑pressure and disconnects
- Optimized **performance for responsive UX**—structured logging, monitoring, and iterative refinement based on metrics
- Delivered **full feature lifecycle**—from prompt engineering through production deployment with observability

---

## License

MIT — see [LICENSE](LICENSE).

---

## Contact

**Jon‑Mark Hampson**  

- GitHub: [@Jon-MarkHampson](https://github.com/Jon-MarkHampson)  
- LinkedIn: [Jon-Mark Hampson](https://www.linkedin.com/in/jon-mark-hampson/)  
- Email: <jonmarkhampson@me.com>

**Project Link:** [GitHub](https://github.com/Jon-MarkHampson/ai-meme-generator)
**Live Demo:** [Website](https://ai-meme-generator-frontend.onrender.com)

---

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/), [Next.js](https://nextjs.org/), [Pydantic AI](https://ai.pydantic.dev/)
- [OpenAI](https://openai.com/), [Anthropic](https://anthropic.com/), [Google](https://ai.google.dev/)
- [Supabase](https://supabase.com/), [Render](https://render.com/)
- [shadcn/ui](https://ui.shadcn.com/), [Radix UI](https://www.radix-ui.com/), [Tailwind CSS](https://tailwindcss.com/)
