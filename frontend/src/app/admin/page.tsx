// frontend/src/app/admin/page.tsx
'use client';

import React from 'react';
import AdminRouteGuard from '@/components/auth/AdminRouteGuard';
import UserManagementTable from '@/components/admin/UserManagementTable'; // Import the new component

const AdminPage: React.FC = () => {
  return (
    <AdminRouteGuard>
      <div className="space-y-8">
        <h1 className="text-3xl font-bold text-[var(--accent)]">Admin Dashboard</h1>

        {/* User Management Section */}
        <section>
          <UserManagementTable />
        </section>

        {/* System Settings Section - Placeholder */}
        <section className="bg-[var(--secondary-background)] p-6 rounded-lg shadow-xl">
          <h2 className="text-2xl font-semibold text-[var(--accent)] mb-4">System Settings</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-[var(--background)] p-4 rounded-md">
              <h3 className="text-lg font-medium text-[var(--accent)] mb-2">API Configuration</h3>
              <p className="text-sm text-[var(--foreground)]">Manage API keys, endpoints, and rate limits. (Placeholder)</p>
              <button className="mt-2 text-sm bg-blue-500 hover:bg-blue-600 text-white py-1 px-3 rounded-md">Configure</button>
            </div>
            <div className="bg-[var(--background)] p-4 rounded-md">
              <h3 className="text-lg font-medium text-[var(--accent)] mb-2">Maintenance Mode</h3>
              <p className="text-sm text-[var(--foreground)]">Enable or disable maintenance mode for the application. (Placeholder)</p>
              <button className="mt-2 text-sm bg-orange-500 hover:bg-orange-600 text-white py-1 px-3 rounded-md">Toggle</button>
            </div>
            <div className="bg-[var(--background)] p-4 rounded-md">
              <h3 className="text-lg font-medium text-[var(--accent)] mb-2">Audit Logs</h3>
              <p className="text-sm text-[var(--foreground)]">View system and user activity logs. (Placeholder)</p>
              <button className="mt-2 text-sm bg-gray-500 hover:bg-gray-600 text-white py-1 px-3 rounded-md">View Logs</button>
            </div>
          </div>
        </section>
      </div>
    </AdminRouteGuard>
  );
};

export default AdminPage;
