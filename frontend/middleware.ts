// frontend/src/middleware.ts
import { NextRequest, NextResponse } from "next/server";
import {
  isProtectedRoute,
  HOME_ROUTE,
  DEFAULT_PROTECTED_ROUTE,
  AUTH_ROUTES,
} from "@/lib/authRoutes";

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const hasAuth = req.cookies.has("access_token");

  // Handle unauthenticated users trying to access protected routes
  if (!hasAuth && isProtectedRoute(pathname)) {
    return NextResponse.redirect(new URL(HOME_ROUTE, req.url));
  }

  // Handle authenticated users trying to access auth pages
  if (hasAuth && AUTH_ROUTES.includes(pathname as any)) {
    // Preserve redirect param if coming from a protected route
    const redirect = req.nextUrl.searchParams.get("redirect");
    const destination =
      redirect && isProtectedRoute(redirect)
        ? redirect
        : DEFAULT_PROTECTED_ROUTE;
    return NextResponse.redirect(new URL(destination, req.url));
  }

  return NextResponse.next();
}

// Let Next.js handle all routes - we'll check protection dynamically
export const config = {
  matcher: "/((?!api|_next/static|_next/image|favicon.ico).*)",
};
