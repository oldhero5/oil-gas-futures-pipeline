// frontend/src/components/Sidebar.tsx
'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { isAdmin, isLoading } = useAuth();

  const navItems = [
    { href: '/', label: 'Overview' },
    { href: '/futures', label: 'Futures Prices' },
    { href: '/options', label: 'Options Analytics' },
    // Add more items as needed
  ];

  const finalNavItems = [...navItems];
  if (isAdmin) {
    finalNavItems.push({ href: '/admin', label: 'Admin Panel' });
  }

  return (
    <aside className="w-64 bg-[var(--secondary-background)] text-[var(--foreground)] p-4 space-y-2 shadow-lg">
      <h2 className="text-lg font-semibold text-[var(--accent)] mb-4">Navigation</h2>
      {isLoading ? (
        <p className="text-sm text-gray-400">Loading navigation...</p>
      ) : (
        finalNavItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block py-2 px-3 rounded-md transition-colors
                ${isActive
                  ? 'bg-[var(--accent)] text-[var(--background)]'
                  : 'hover:bg-[var(--border-color)] hover:text-[var(--accent)]'
                }
              `}
            >
              {item.label}
            </Link>
          );
        })
      )}
    </aside>
  );
};

export default Sidebar;
