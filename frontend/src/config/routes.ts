/**
 * Core route definitions
 */
export const PROTECTED_ROUTES = ["/generate", "/profile", "/gallery"] as const;
export const PUBLIC_ROUTES = ["/", "/login", "/signup"] as const;
export const AUTH_ROUTES = ["/login", "/signup"] as const;
export const DEFAULT_PROTECTED_ROUTE = "/generate";
export const LOGIN_ROUTE = "/login";
export const HOME_ROUTE = "/";

/**
 * Check if a pathname requires authentication
 */
export function isProtectedRoute(pathname: string): boolean {
  return PROTECTED_ROUTES.some((route) => pathname.startsWith(route));
}

/**
 * Check if a pathname is publicly accessible
 */
export function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.some(route => route === pathname);
}

/**
 * Get login URL with optional redirect
 */
export function getLoginUrl(redirectTo?: string): string {
  if (!redirectTo || isPublicRoute(redirectTo)) {
    return LOGIN_ROUTE;
  }

  const params = new URLSearchParams({ redirect: redirectTo });
  return `${LOGIN_ROUTE}?${params}`;
}

/**
 * Get redirect path after login
 */
export function getPostLoginRedirect(
  requestedPath?: string | null,
  searchParams?: URLSearchParams
): string {
  // Check URL params first
  const redirectParam = searchParams?.get("redirect");
  if (redirectParam && isProtectedRoute(redirectParam)) {
    return redirectParam;
  }

  // Check requested path
  if (requestedPath && isProtectedRoute(requestedPath)) {
    return requestedPath;
  }

  return DEFAULT_PROTECTED_ROUTE;
}
