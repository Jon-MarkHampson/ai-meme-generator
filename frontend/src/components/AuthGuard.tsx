// AuthGuard.tsx - Simplified for consistent server/client rendering
'use client';
import { PropsWithChildren, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { isPublicRoute } from '@/lib/authRoutes';

export function AuthGuard({ children }: PropsWithChildren) {
    const { user, loading } = useAuth();
    const router = useRouter();
    const pathname = usePathname();
    const isPublic = isPublicRoute(pathname);

    // Handle auth redirects after loading is complete
    useEffect(() => {
        if (loading) return; // Wait for auth to finish loading

        if (!isPublic && !user) {
            // Protected route but no user - redirect to login
            router.replace('/login?auth=required');
        } else if (isPublic && user && pathname === '/') {
            // User on home page - redirect to app
            router.replace('/generate');
        }
    }, [loading, isPublic, user, router, pathname]);

    // Always render children immediately to prevent hydration mismatches
    // Let the auth redirects handle navigation in useEffect
    return <>{children}</>;
}
