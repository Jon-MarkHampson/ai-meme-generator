// AuthGuard.tsx
'use client';
import { PropsWithChildren, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { PUBLIC_ROUTES } from '@/lib/authRoutes';

export function AuthGuard({ children }: PropsWithChildren) {
    const { user, loading } = useAuth();
    const router = useRouter();
    const pathname = usePathname();
    const isPublic = PUBLIC_ROUTES.includes(pathname as (typeof PUBLIC_ROUTES)[number]);

    useEffect(() => {
        if (!isPublic && !loading && !user) {
            router.replace('/');          // soft-redirect for in-app expiry
        }
    }, [isPublic, loading, user, router]);

    return <>{children}</>;
}