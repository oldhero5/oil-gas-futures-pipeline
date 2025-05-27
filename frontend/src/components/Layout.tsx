// frontend/src/components/Layout.tsx
'use client';

import React, { ReactNode, useEffect } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter, usePathname } from 'next/navigation';

interface LayoutProps {
  children: ReactNode;
}

const PUBLIC_PATHS = ['/login', '/register']; // Define public paths

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (isLoading) {
      return; // Don't do anything while auth status is loading
    }

    const pathIsPublic = PUBLIC_PATHS.includes(pathname);

    if (!user && !pathIsPublic) {
      // User is not logged in and not on a public page, redirect to login
      router.replace('/login');
    } else if (user && pathIsPublic) {
      // User is logged in but on a public page (e.g., /login), redirect to dashboard
      router.replace('/');
    }
  }, [user, isLoading, router, pathname]);

  // Show loading state or a minimal layout while redirecting or loading auth
  if (isLoading || (!user && !PUBLIC_PATHS.includes(pathname))) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[var(--background)] text-[var(--foreground)]">
        <p>Loading application...</p>
      </div>
    );
  }

  // If user is logged in OR on a public page (and not loading), show the full layout
  return (
    <div className="flex flex-col min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <Header />
      <div className="flex flex-1 pt-16"> {/* Adjust pt-16 if header height changes */}
        <Sidebar />
        <main className="flex-1 p-6 ml-64"> {/* Adjust ml-64 if sidebar width changes */}
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
