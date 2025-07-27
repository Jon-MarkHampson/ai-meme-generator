// frontend/src/components/AuthGuard.tsx
"use client";

import { useSession } from "@/contexts/SessionContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function AuthGuard({ children, fallback }: AuthGuardProps) {
  const { state } = useSession();
  const router = useRouter();

  // Redirect unauthenticated users to login
  useEffect(() => {
    if (!state.isValidating && !state.isAuthenticated) {
      router.push("/login");
    }
  }, [state.isValidating, state.isAuthenticated, router]);

  // Show loading while validating
  if (state.isValidating) {
    return (
      fallback || (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      )
    );
  }

  // If not authenticated, show nothing (redirect is in progress)
  if (!state.isAuthenticated) {
    return null;
  }

  // User is authenticated, show content
  return <>{children}</>;
}
