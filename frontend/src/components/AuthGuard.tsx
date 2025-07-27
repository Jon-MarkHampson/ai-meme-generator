// frontend/src/components/AuthGuard.tsx
"use client";

import { useSession } from "@/contexts/SessionContext";

interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function AuthGuard({ children, fallback }: AuthGuardProps) {
  const { state } = useSession();

  // Show loading while validating or if not authenticated
  if (state.isValidating || !state.isAuthenticated) {
    return (
      fallback || (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      )
    );
  }

  // User is authenticated, show content
  return <>{children}</>;
}
