// authRoutes.ts - Single source of truth for auth routing logic
export const PROTECTED_ROUTES = [
  "/generate/:path*",
  "/profile/:path*",
  "/gallery/:path*",
];

export const PUBLIC_ROUTES = ["/", "/login", "/signup"];
export const DEFAULT_PROTECTED_ROUTE = "/generate";

/**
 * Check if a given pathname is a public route
 */
export function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.includes(pathname);
}

/**
 * Check if a given pathname is a protected route
 * Handles pattern matching for routes with :path* wildcards
 */
export function isProtectedRoute(pathname: string): boolean {
  // First check exact matches in public routes
  if (isPublicRoute(pathname)) {
    return false;
  }

  // Check if it matches any protected route pattern
  return PROTECTED_ROUTES.some((route) => {
    if (route.includes("/:path*")) {
      // Convert route pattern to a prefix match
      const baseRoute = route.replace("/:path*", "");
      return pathname.startsWith(baseRoute);
    }
    return pathname === route;
  });
}

/**
 * Clears authentication cookies
 */
export function clearAuthCookies(): void {
  if (typeof window === "undefined") return;

  document.cookie =
    "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
  document.cookie =
    "refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
}
