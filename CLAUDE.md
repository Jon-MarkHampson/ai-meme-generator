# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Meme Generator is a full-stack application that creates AI-powered memes through an interactive chat interface. Users can generate contextual memes with appropriate templates and text overlays selected by AI agents.

## Development Commands

### Backend (Python/FastAPI)
Located in `/backend/` directory:

```bash
# Install dependencies (requires uv package manager)
uv sync

# Start development server
uvicorn main:app --reload --app-dir .

# Backend runs on http://localhost:8000
# API documentation: http://localhost:8000/docs
```

### Frontend (Next.js)
Located in `/frontend/` directory:

```bash
# Install dependencies
npm install

# Start development server with Turbopack
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linting
npm run lint

# Frontend runs on http://localhost:3000
```

## Architecture

### Backend Structure (Features-based)
- **`features/auth/`**: JWT authentication with HTTP-only cookies, session management, refresh tokens
- **`features/generate/`**: AI meme generation using agent-based workflow (manager_agent → text_generation_agent)
- **`features/user_memes/`**: Meme storage, favorites management, user collections
- **`features/llm_providers/`**: Abstraction layer for OpenAI and Anthropic providers
- **`features/image_storage/`**: Supabase storage integration for meme images
- **`features/conversations/`**: Chat conversation persistence and management
- **`features/messages/`**: Message history tracking for conversations
- **`features/users/`**: User profile CRUD operations
- **`database/`**: SQLModel configuration with Supabase PostgreSQL
- **`utils/`**: Password hashing, security utilities
- **Monitoring**: Logfire instrumentation throughout

### Frontend Structure (Next.js 15 App Router)
- **`src/types/`**: Centralized TypeScript type definitions
- **`src/services/`**: API client functions with Axios
- **`src/config/`**: Application configuration (routes, AI models)
- **`src/utils/`**: Utility functions (cn, sessionToasts)
- **`src/contexts/`**: SessionContext for auth state management
- **`src/hooks/`**: Custom React hooks
- **`src/components/`**: Reusable components
- **`src/components/ui/`**: shadcn/ui primitives
- **`src/app/`**: Next.js app router pages

### Authentication System

**Backend Flow:**
1. Login/signup creates JWT access token (15min) + refresh token (7days)
2. Tokens stored as HTTP-only cookies
3. `/auth/refresh` endpoint renews access token
4. All protected endpoints validate JWT via `get_current_active_user` dependency

**Frontend Flow:**
1. `middleware.ts`: Initial route protection checking for access_token cookie
2. `SessionContext`: Central state management with multi-timer system
   - Inactivity timer: 4 minutes (warns after 3 minutes)
   - Warning period: 60 seconds before logout
   - Auto-refresh: Every 2 minutes for active users
3. `AuthGuard` component: Page-level protection wrapper
4. Global 401 handler: Custom window event triggers logout

### Meme Generation Pipeline

1. User sends prompt through chat interface
2. Frontend calls `/generate/meme` with streaming response
3. Backend workflow:
   - Manager agent analyzes prompt and selects meme template
   - Text generation agent creates appropriate captions
   - Image service overlays text on template using Pillow
   - Generated meme uploaded to Supabase storage
4. Response streamed back as Server-Sent Events
5. Frontend displays meme with markdown support

### Key Dependencies

**Backend:**
- FastAPI with uvicorn
- Pydantic AI for agent orchestration
- SQLModel for database ORM
- Supabase for storage and database
- Pillow for image manipulation
- Logfire for observability

**Frontend:**
- Next.js 15 with Turbopack
- TypeScript for type safety
- Tailwind CSS v4 for styling
- shadcn/ui components
- Axios with retry logic
- React Hook Form + Zod validation

### Environment Variables

**Backend (.env):**
- `OPENAI_API_KEY`: OpenAI provider access
- `ANTHROPIC_API_KEY`: Anthropic provider access
- `DATABASE_URL`: PostgreSQL connection string
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anon key
- `JWT_SECRET_KEY`: JWT signing secret
- `JWT_REFRESH_SECRET_KEY`: Refresh token secret
- `LOGFIRE_TOKEN`: Monitoring service token

**Frontend (.env.local):**
- `NEXT_PUBLIC_API_BASE_URL`: Backend API URL (default: http://localhost:8000)
- `NEXT_PUBLIC_BASE_URL`: Frontend URL (default: http://localhost:3000)

### Model Configuration

AI models are configured in `frontend/src/config/ai-models.ts` with availability checked via backend endpoint `/llm_providers/availability/simple`. The system supports:
- OpenAI: GPT-4o, GPT-4.1, GPT-4.1-mini, O1-mini
- Anthropic: Claude Sonnet 4, Claude 3.7, Claude 3.5

### Database Schema

Using SQLModel with these main tables:
- `users`: User accounts with profile information
- `conversations`: Chat conversation containers
- `messages`: Individual messages within conversations
- `user_memes`: Generated memes linked to users
- `meme_templates`: Pre-defined meme template library
- `caption_variants`: Text overlays for memes