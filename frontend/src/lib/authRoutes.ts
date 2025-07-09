// auth-routes.ts
export const PROTECTED_ROUTES = [
  "/generate/:path*",
  "/profile/:path*",
  "/gallery/:path*",
];

export const PUBLIC_ROUTES = ["/", "/login", "/signup"];
