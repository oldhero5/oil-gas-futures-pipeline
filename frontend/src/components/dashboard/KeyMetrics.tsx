// frontend/src/components/dashboard/KeyMetrics.tsx
import React from 'react';

const KeyMetrics: React.FC = () => {
  return (
    <div className="bg-[var(--secondary-background)] p-6 rounded-lg shadow-lg">
      <h2 className="text-xl font-semibold text-[var(--accent)] mb-4">Key Metrics</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Placeholder Metric Cards */}
        <div className="bg-[var(--background)] p-4 rounded shadow">
          <h3 className="text-lg text-[var(--foreground)]">Total Trades</h3>
          <p className="text-2xl font-bold text-[var(--accent)]">1,234</p>
        </div>
        <div className="bg-[var(--background)] p-4 rounded shadow">
          <h3 className="text-lg text-[var(--foreground)]">Market Sentiment</h3>
          <p className="text-2xl font-bold text-green-400">Bullish</p>
        </div>
        <div className="bg-[var(--background)] p-4 rounded shadow">
          <h3 className="text-lg text-[var(--foreground)]">Active Alerts</h3>
          <p className="text-2xl font-bold text-red-400">5</p>
        </div>
        <div className="bg-[var(--background)] p-4 rounded shadow">
          <h3 className="text-lg text-[var(--foreground)]">System Uptime</h3>
          <p className="text-2xl font-bold text-green-400">99.9%</p>
        </div>
      </div>
    </div>
  );
};

export default KeyMetrics;
