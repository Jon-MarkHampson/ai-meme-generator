// middleware.ts
import { NextRequest, NextResponse } from "next/server";
import { isTokenExpired, decodeJWT, type JWTPayload } from "@/lib/authUtils";

// Enhanced helper with better logging and cleanup
function redirectToIndex(req: NextRequest, reason: string) {
  const url = req.nextUrl.clone();
  url.pathname = "/";

  // Add query param to indicate session expiry for UX
  if (reason === "expired") {
    url.searchParams.set("session", "expired");
  }

  const response = NextResponse.redirect(url);

  // Clear all auth-related cookies
  response.cookies.set("access_token", "", {
    maxAge: 0,
    path: "/",
    secure: process.env.NODE_ENV === "production",
    httpOnly: true,
    sameSite: "strict",
  });

  // Clear any other auth cookies if they exist
  response.cookies.set("refresh_token", "", {
    maxAge: 0,
    path: "/",
    secure: process.env.NODE_ENV === "production",
    httpOnly: true,
    sameSite: "strict",
  });

  return response;
}

export function middleware(req: NextRequest) {
  // Define protected routes - these should match the routes in authRoutes.ts
  const protectedRoutes = ["/generate", "/profile", "/gallery"];

  // Check if current path needs protection
  const needsAuth = protectedRoutes.some((route) =>
    req.nextUrl.pathname.startsWith(route)
  );

  if (!needsAuth) {
    return NextResponse.next();
  }

  const token = req.cookies.get("access_token")?.value;

  // 1) No token → redirect to index
  if (!token) {
    return redirectToIndex(req, "missing");
  }

  // 2) Validate token structure and expiry
  if (isTokenExpired(token, 30)) {
    return redirectToIndex(req, "expired");
  }

  try {
    const payload = decodeJWT(token);

    // Check if token has required fields
    if (!payload || !payload.exp || !payload.sub) {
      throw new Error("Invalid token structure");
    }

    // Optional: Check if token is too old (issued more than X hours ago)
    const currentTime = Math.floor(Date.now() / 1000);
    if (payload.iat && currentTime - payload.iat > 24 * 60 * 60) {
      // 24 hours
      throw new Error("Token too old");
    }
  } catch (error) {
    // Log the error reason for debugging (in production, use proper logging)
    console.warn(
      `Session validation failed: ${
        error instanceof Error ? error.message : "Unknown error"
      }`
    );
    return redirectToIndex(req, "expired");
  }

  // 3) Valid token → allow request through
  return NextResponse.next();
}

// Static config that Next.js can parse at build time
export const config = {
  matcher: ["/generate/:path*", "/profile/:path*", "/gallery/:path*"],
};
