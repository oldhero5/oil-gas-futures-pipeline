// frontend/src/components/Header.tsx
'use client'; // Required for hooks like useAuth

import React from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

const Header: React.FC = () => {
  const { user, logout, isLoading } = useAuth();

  return (
    <header className="bg-[var(--secondary-background)] text-[var(--foreground)] p-4 shadow-md border-b border-[var(--border-color)]">
      <div className="container mx-auto flex justify-between items-center">
        <h1 className="text-xl font-semibold text-[var(--accent)]">Oil & Gas Futures Pipeline</h1>
        <div>
          {isLoading ? (
            <span className="text-sm text-[var(--foreground)]">Loading...</span>
          ) : user ? (
            <div className="flex items-center space-x-4">
              <span className="text-sm">Welcome, {user.email}</span>
              <button
                onClick={logout}
                className="bg-red-500 hover:bg-red-600 text-white py-1 px-3 rounded-md text-sm"
              >
                Logout
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="bg-[var(--accent)] hover:bg-cyan-500 text-[var(--background)] py-1 px-3 rounded-md text-sm transition-colors"
            >
              Login
            </Link>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
