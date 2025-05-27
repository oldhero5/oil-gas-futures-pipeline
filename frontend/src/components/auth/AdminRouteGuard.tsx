// frontend/src/components/auth/AdminRouteGuard.tsx
'use client';

import React, { ReactNode } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

interface AdminRouteGuardProps {
  children: ReactNode;
}

const AdminRouteGuard: React.FC<AdminRouteGuardProps> = ({ children }) => {
  const { user, isAdmin, isLoading } = useAuth();
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-lg text-[var(--foreground)]">Loading authentication status...</p>
      </div>
    );
  }

  if (!user) {
    // User not logged in, redirect to login
    // You might want to store the intended destination to redirect back after login
    if (typeof window !== 'undefined') { // Ensure router.push is called client-side
        router.push('/login');
    }
    return (
        <div className="flex items-center justify-center h-screen">
          <p className="text-lg text-[var(--foreground)]">Redirecting to login...</p>
        </div>
      ); // Or a loading spinner while redirecting
  }

  if (!isAdmin) {
    // User is logged in but not an admin
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-[var(--background)] text-[var(--foreground)] p-4">
        <h1 className="text-3xl font-bold text-red-500 mb-4">Access Denied</h1>
        <p className="text-lg mb-6">You do not have permission to view this page.</p>
        <button
          onClick={() => router.push('/')}
          className="bg-[var(--accent)] text-[var(--background)] py-2 px-4 rounded-md hover:bg-cyan-500 transition-colors"
        >
          Go to Dashboard
        </button>
      </div>
    );
  }

  // User is logged in and is an admin
  return <>{children}</>;
};

export default AdminRouteGuard;
