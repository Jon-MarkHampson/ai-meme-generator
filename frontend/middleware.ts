// frontend/src/middleware.ts
import { NextRequest, NextResponse } from "next/server";
import {
  isProtectedRoute,
  HOME_ROUTE,
  DEFAULT_PROTECTED_ROUTE,
  AUTH_ROUTES,
} from "@/config/routes";

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const hasAuth = req.cookies.has("access_token");

  // Only redirect to login if trying to access protected routes without cookie
  // Let SessionContext handle validation for auth pages - don't redirect here
  if (!hasAuth && isProtectedRoute(pathname)) {
    const loginUrl = new URL("/login", req.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

// Let Next.js handle all routes - we'll check protection dynamically
export const config = {
  matcher: "/((?!api|_next/static|_next/image|favicon.ico).*)",
};
