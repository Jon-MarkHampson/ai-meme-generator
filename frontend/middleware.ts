// middleware.ts
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { jwtDecode } from "jwt-decode";

interface JWTPayload {
  exp: number;
  // any other claims you set…
}

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // 1) Whitelist anything that shouldn't require auth
  const publicPatterns = [
    "/login",
    "/signup",
    "/favicon.ico",
    "/_next/", // Next.js asset loader
    "/api/public/", // if you have truly public API routes
  ];
  if (publicPatterns.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // 2) Grab the token cookie
  const token = req.cookies.get("access_token")?.value;
  if (!token) {
    const url = req.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url);
  }

  // 3) Decode & check expiry
  try {
    const { exp } = jwtDecode<JWTPayload>(token);
    if (exp * 1000 < Date.now()) throw new Error("expired");
  } catch {
    const url = req.nextUrl.clone();
    url.pathname = "/login";
    const res = NextResponse.redirect(url);
    // Clear the stale token cookie
    res.cookies.set("access_token", "", { maxAge: 0, path: "/" });
    return res;
  }

  // 4) All good → continue
  return NextResponse.next();
}

// Only run on the routes you actually need protected:
export const config = {
  matcher: [
    "/generate",
    "/generate/:path*",
    "/profile/:path*",
    "/settings/:path*",
  ],
};
