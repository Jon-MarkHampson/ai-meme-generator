// src/components/AuthGuard.tsx
'use client';
import { useEffect, PropsWithChildren } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { getSession } from '@/lib/auth';

export function AuthGuard({ children }: PropsWithChildren) {
    const router = useRouter();
    const pathname = usePathname();
    useEffect(() => {
        if (pathname === '/login') return;
        getSession().then(sess => {
            if (!sess) router.replace('/login');
        });
    }, [pathname, router]);
    return <>{children}</>;
}