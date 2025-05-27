// frontend/src/components/dashboard/SystemStatus.tsx
import React from 'react';

const StatusIndicator: React.FC<{ isOnline: boolean }> = ({ isOnline }) => (
  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${isOnline ? 'bg-green-500 text-green-900' : 'bg-red-500 text-red-100'}`}>
    {isOnline ? 'Online' : 'Offline'}
  </span>
);

const SystemStatus: React.FC = () => {
  // Placeholder system status data
  const services = [
    { name: 'Data Ingestion API', online: true },
    { name: 'Pricing Engine', online: true },
    { name: 'Database Service', online: true },
    { name: 'Real-time Feed', online: false },
  ];

  return (
    <div className="bg-[var(--secondary-background)] p-6 rounded-lg shadow-lg mt-6">
      <h2 className="text-xl font-semibold text-[var(--accent)] mb-4">System Status</h2>
      <ul className="space-y-3">
        {services.map(service => (
          <li key={service.name} className="flex justify-between items-center bg-[var(--background)] p-3 rounded shadow">
            <span className="text-[var(--foreground)]">{service.name}</span>
            <StatusIndicator isOnline={service.online} />
          </li>
        ))}
      </ul>
    </div>
  );
};

export default SystemStatus;
