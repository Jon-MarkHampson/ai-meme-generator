# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Start development server with Turbopack
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linting
npm run lint
```

Development server runs on http://localhost:3000

## Project Architecture

### Authentication & Session Management

This app uses a sophisticated cookie-based authentication system with multiple layers:

1. **Middleware** (`middleware.ts`) - Initial route protection checking for `access_token` cookie
2. **SessionContext** (`src/contexts/SessionContext.tsx`) - Central session state management with:
   - Multi-timer system (inactivity: 4min, warning: 60s, refresh: 2min)
   - Activity tracking (keydown, touchstart, click events)
   - Automatic token refresh for active users
   - Race condition prevention with `refreshInProgressRef`
3. **AuthGuard** component - Page-level protection that redirects unauthenticated users
4. **API interceptor** (`src/lib/api.ts`) - Global 401 handling via custom window events

**Key Files:**
- `src/contexts/SessionContext.tsx` - Core session management logic
- `src/components/AuthGuard.tsx` - Route protection component
- `src/lib/auth.ts` - Authentication API services
- `src/constants/sessionConfig.ts` - Timing configuration

### API Integration Patterns

**Centralized API Client** (`src/lib/api.ts`):
- Axios with `withCredentials: true` for cookie handling
- Response interceptor for global authentication error handling
- Custom event system (`window.dispatchEvent('session-expired')`)

**Service Layer:**
- `src/lib/auth.ts` - User authentication and profile management
- `src/lib/generate.ts` - AI conversation and streaming chat
- `src/lib/gallery.ts` - Meme favorites and collections

**Streaming Architecture:**
- Server-Sent Events for real-time AI responses
- Fetch-based streaming with manual parsing
- Abort controllers for request cancellation
- Dual message types: chat messages + conversation metadata

### Component Organization

**Structure:**
- `src/components/ui/` - Reusable UI primitives (shadcn/ui)
- `src/components/` - Feature-specific business components
- `src/app/*/page.tsx` - Route-specific page components

**Key Patterns:**
- Guard Pattern: `AuthGuard` for route protection  
- Provider Pattern: `SessionProvider` wraps entire app
- Compound Components: Chat interface (sidebar + input + bubbles)

### Configuration Management

**Core Config Files:**
- `src/config/models.ts` - AI model definitions with capabilities, pricing, availability
- `src/constants/sessionConfig.ts` - Session timing constants (supports dev/prod modes)
- `src/lib/authRoutes.ts` - Centralized route definitions

**Model Management:**
- Dynamic availability checking with backend
- Caching with TTL (5 minutes)
- Debug utilities (development only)

### State Management

**Hybrid Approach:**
- React Context for global auth state (SessionContext)
- Local state with hooks for component data
- Custom hooks: `useModelSelection`, `useSession`
- localStorage for user preferences (selected AI model)

### Security Considerations

**XSS Prevention:**
- URL sanitization in `ChatBubble` component before rendering markdown
- HTTP-only cookies for token storage
- Protocol validation (only http/https allowed)

**Session Security:**
- Automatic logout on inactivity
- Cross-tab session synchronization
- Race condition prevention in token refresh
- Graceful 401 error handling without redirect loops

### Development Notes

**Environment Variables:**
- `NEXT_PUBLIC_API_BASE_URL` - Backend API endpoint
- `NEXT_PUBLIC_BASE_URL` - Frontend base URL

**Image Handling:**
- Next.js Image component configured for Supabase storage
- Remote patterns configured for hostname: `samqtcnjpkhfysgxbakn.supabase.co`

**Testing Session Timers:**
- Toggle `useShortTimers` in `src/constants/sessionConfig.ts` for faster testing
- Short timers: 10s inactivity, 10s warning, 8s refresh
- Production timers: 4min inactivity, 60s warning, 2min refresh

### Common Issues

**Session Management:**
- If users are logged out unexpectedly, check for race conditions in `refreshSession`
- Warning toasts not showing: verify timing coordination between inactivity and refresh timers
- Multiple refresh attempts: ensure `refreshInProgressRef` is properly managed

**Authentication Flow:**
- AuthGuard should redirect (not show loading) for unauthenticated users
- Home page should show different content based on authentication state
- API 401 errors should trigger `session-expired` events, not direct redirects