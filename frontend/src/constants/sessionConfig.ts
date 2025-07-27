// frontend/src/constants/sessionConfig.ts

// const isDev = process.env.NODE_ENV === "development";
const isDev = true;
/**
 * Session timing configuration
 */
export const SESSION_TIMING = {
  // Time before showing warning
  INACTIVITY_TIMEOUT: isDev ? 30_000 : 5 * 60_000, // 30s dev, 5min prod

  // Countdown duration
  WARNING_DURATION: isDev ? 30_000 : 30_000, // 30s both

  // How often to refresh session when active
  REFRESH_INTERVAL: 4 * 60_000, // 4 minutes
} as const;

/**
 * Activity events to track
 */
export const ACTIVITY_EVENTS = [
  "mousemove",
  "keydown",
  "touchstart",
  "click",
] as const;
