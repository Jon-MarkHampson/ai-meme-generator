// middleware.ts - Simplified for HTTP-only cookie auth
import { NextRequest, NextResponse } from "next/server";
import { PROTECTED_ROUTES } from "@/lib/authRoutes";

export function middleware(req: NextRequest) {
  // Check if current path needs protection
  const needsAuth = PROTECTED_ROUTES.some((route) => {
    const baseRoute = route.replace("/:path*", "");
    return req.nextUrl.pathname.startsWith(baseRoute);
  });

  if (!needsAuth) {
    return NextResponse.next();
  }

  // Check if we have an auth cookie (basic check only)
  const hasAuthCookie = req.cookies.get("access_token");

  // If no auth cookie, redirect to login
  if (!hasAuthCookie) {
    const url = req.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("auth", "required");
    return NextResponse.redirect(url);
  }

  // Let the request through - server will validate the actual token
  return NextResponse.next();
}

// Use the same routes as defined in authRoutes.ts
export const config = {
  matcher: ["/generate/:path*", "/profile/:path*", "/gallery/:path*"],
};
