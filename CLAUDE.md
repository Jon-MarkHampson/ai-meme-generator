# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Meme Generator is a full-stack application that allows users to interactively create memes powered by AI. The project consists of:

- **Backend**: FastAPI application with SQLModel, Supabase integration, and multiple AI providers (OpenAI, Anthropic)
- **Frontend**: Next.js 15 React application with TypeScript, Tailwind CSS, and shadcn/ui components

## Development Commands

### Backend (Python/FastAPI)
Located in `/backend/` directory:

```bash
# Install dependencies
uv sync

# Start development server
uvicorn main:app --reload --app-dir .

# The backend runs on http://localhost:8000 by default
# API docs available at http://localhost:8000/docs
```

### Frontend (Next.js)
Located in `/frontend/` directory:

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint

# The frontend runs on http://localhost:3000 by default
```

## Architecture

### Backend Structure
- **Features-based architecture**: Each feature has its own controller, service, and models
- **Main modules**:
  - `features/auth/`: User authentication with JWT and session management
  - `features/generate/`: AI-powered meme generation with agent-based workflow
  - `features/user_memes/`: User meme storage and management
  - `features/llm_providers/`: Multi-provider AI service abstraction (OpenAI, Anthropic)
  - `features/image_storage/`: Image upload and storage service
  - `features/conversations/`: Chat conversation management
  - `features/messages/`: Message history tracking
  - `features/users/`: User profile management
  - `utils/`: Shared utilities including password hashing and security functions
- **Database**: SQLModel with Supabase PostgreSQL backend
- **AI Integration**: Pydantic AI with multiple LLM providers
- **Observability**: Logfire instrumentation for monitoring

### Frontend Structure
- **App Router**: Next.js 15 with app directory structure
- **Authentication**: Multi-layered session management with JWT tokens
  - Middleware for initial route protection
  - SessionContext for central state management
  - AuthGuard component for page-level protection
  - Global 401 handler via custom events
- **UI Components**: shadcn/ui with Radix primitives and Tailwind CSS v4
- **State Management**: React Context for session and global state
- **API Integration**: Axios with automatic retry and 401 handling

### Key Features
- **AI Meme Generation**: Multi-step agent workflow for creating contextual memes
- **Template System**: 100+ pre-built classic meme templates with text overlay
- **User Management**: Registration, login, profile management
- **Gallery**: Browse and favorite generated memes
- **Model Selection**: Choose between different AI providers and models
- **Real-time Streaming**: Server-Sent Events for AI response streaming

### Authentication Flow
- Users authenticate via `/auth/login` or `/auth/signup` endpoints
- JWT tokens stored in HTTP-only cookies with refresh token mechanism  
- Frontend uses multi-timer session management (inactivity, warning, refresh)
- Auth routes are protected with middleware and AuthGuard component
- Cross-tab session synchronization for consistent auth state

### Meme Generation Process
1. User inputs prompt via chat interface
2. Manager agent analyzes prompt and selects appropriate meme template
3. Text generation agent creates meme text based on template and context
4. Image service overlays text onto selected template
5. Generated meme is stored and returned to user

## Environment Setup
- Backend requires environment variables for AI provider API keys, database connection, JWT secrets, and Logfire token
- Frontend requires `NEXT_PUBLIC_API_BASE_URL` and `NEXT_PUBLIC_BASE_URL` for API communication
- Both services use `.env` files for configuration

## Testing
Currently no test setup exists. When adding tests:
- Backend: Use pytest with FastAPI test client
- Frontend: Consider Jest/Vitest for unit tests and Playwright for E2E tests