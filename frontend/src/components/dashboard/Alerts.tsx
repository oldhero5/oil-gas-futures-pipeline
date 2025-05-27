// frontend/src/components/dashboard/Alerts.tsx
import React from 'react';

const Alerts: React.FC = () => {
  // Placeholder alert data
  const alerts = [
    { id: 1, message: 'Crude Oil WTI price reached $75.50', severity: 'warning' },
    { id: 2, message: 'Natural Gas inventory report due tomorrow', severity: 'info' },
    { id: 3, message: 'High volatility detected in Brent Crude', severity: 'critical' },
  ];

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'warning': return 'bg-yellow-500 text-yellow-900';
      case 'info': return 'bg-blue-500 text-blue-100';
      case 'critical': return 'bg-red-600 text-red-100';
      default: return 'bg-gray-500 text-gray-100';
    }
  };

  return (
    <div className="bg-[var(--secondary-background)] p-6 rounded-lg shadow-lg mt-6">
      <h2 className="text-xl font-semibold text-[var(--accent)] mb-4">Alerts</h2>
      <div className="space-y-3">
        {alerts.map(alert => (
          <div key={alert.id} className={`p-3 rounded shadow ${getSeverityColor(alert.severity)}`}>
            <p className="font-medium">{alert.message}</p>
          </div>
        ))}
        {alerts.length === 0 && (
          <p className="text-[var(--foreground)]">No active alerts.</p>
        )}
      </div>
    </div>
  );
};

export default Alerts;
