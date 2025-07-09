// authUtils.ts
import { jwtDecode } from "jwt-decode";

export interface JWTPayload {
  exp: number;
  iat?: number;
  sub?: string;
}

/**
 * Safely decodes a JWT token and returns its payload
 */
export function decodeJWT(token: string): JWTPayload | null {
  try {
    return jwtDecode<JWTPayload>(token);
  } catch (error) {
    console.error("Error decoding JWT:", error);
    return null;
  }
}

/**
 * Checks if a JWT token is expired
 */
export function isTokenExpired(
  token: string,
  gracePeriodSeconds: number = 0
): boolean {
  const payload = decodeJWT(token);
  if (!payload || !payload.exp) return true;

  const currentTime = Math.floor(Date.now() / 1000);
  return payload.exp < currentTime + gracePeriodSeconds;
}

/**
 * Gets the time remaining before a token expires (in seconds)
 */
export function getTokenTimeRemaining(token: string): number | null {
  const payload = decodeJWT(token);
  if (!payload || !payload.exp) return null;

  const currentTime = Math.floor(Date.now() / 1000);
  return payload.exp - currentTime;
}

/**
 * Extracts the access token from browser cookies
 */
export function getAccessTokenFromCookies(): string | null {
  if (typeof window === "undefined") return null;

  const token = document.cookie
    .split("; ")
    .find((row) => row.startsWith("access_token="))
    ?.split("=")[1];

  return token || null;
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

/**
 * Checks if current path is a public route
 */
export function isPublicRoute(pathname: string): boolean {
  const publicRoutes = ["/", "/login", "/signup"];
  return publicRoutes.includes(pathname);
}
