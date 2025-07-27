// frontend/src/constants/sessionConfig.ts

// Set to true for testing, false for normal operation
const useShortTimers = false;

/**
 * Session timing configuration
 */
export const SESSION_TIMING = {
  // Time before showing warning (4min + 1min warning = 5min total to match backend)
  INACTIVITY_TIMEOUT: useShortTimers ? 10_000 : 4 * 60_000, // 10s testing, 4min normal

  // Countdown duration
  WARNING_DURATION: useShortTimers ? 10_000 : 60_000, // 10s testing, 60s normal

  // How often to refresh session when active
  REFRESH_INTERVAL: useShortTimers ? 8_000 : 2 * 60_000, // 8s testing, 2min normal (frequent refresh for active users)
} as const;

/**
 * Activity events to track
 */
export const ACTIVITY_EVENTS = [
  // "mousemove",
  "keydown",
  "touchstart",
  "click",
] as const;
