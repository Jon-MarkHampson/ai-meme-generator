// middleware.ts
import { NextRequest, NextResponse } from "next/server";
import { jwtDecode } from "jwt-decode";
import { PROTECTED_ROUTES } from "@/lib/authRoutes";

interface JWTPayload {
  exp: number; // add any other custom claims as needed
}

// Small helper to keep the main flow clean
function redirectHome(req: NextRequest) {
  const url = req.nextUrl.clone();
  url.pathname = "/";
  return NextResponse.redirect(url);
}

export function middleware(req: NextRequest) {
  const token = req.cookies.get("access_token")?.value;

  // 1) No cookie → bounce to index
  if (!token) return redirectHome(req);

  // 2) Check expiry (basic “exp” claim)
  try {
    const { exp } = jwtDecode<JWTPayload>(token);
    // Optional 30-second grace to smooth out clock skew:
    if (exp * 1000 < Date.now() - 30_000) throw new Error("expired");
  } catch {
    const res = redirectHome(req);
    // Clear the stale cookie so the browser stops sending it
    res.cookies.set("access_token", "", { maxAge: 0, path: "/" });
    return res;
  }

  // 3) Valid token → allow request through
  return NextResponse.next();
}

// Protect only the pages that need auth
export const config = { matcher: PROTECTED_ROUTES };
