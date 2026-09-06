'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';

const PUBLIC_PATHS = ['/login'];

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const isPublic = PUBLIC_PATHS.includes(pathname);

  useEffect(() => {
    if (!isAuthenticated && !isPublic) {
      router.replace('/login');
    }
  }, [isAuthenticated, isPublic, router]);

  if (!isAuthenticated && !isPublic) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-accent font-mono-tech animate-pulse text-xs">Redirecting to login...</div>
      </div>
    );
  }

  if (isPublic && !isAuthenticated) {
    return <>{children}</>;
  }

  return <>{children}</>;
}
