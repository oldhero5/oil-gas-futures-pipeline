// frontend/src/app/options/page.tsx
'use client';

import React from 'react';
import OptionsAnalyticsDisplay from '@/components/dashboard/OptionsAnalyticsDisplay';

const OptionsPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold text-[var(--accent)]">Options Analytics Dashboard</h1>

      <section>
        <OptionsAnalyticsDisplay />
      </section>

      {/* Placeholder for additional options tools or visualizations */}
      <section className="bg-[var(--secondary-background)] p-6 rounded-lg shadow-xl">
        <h2 className="text-2xl font-semibold text-[var(--accent)] mb-4">Strategy Builder & Risk Analysis (Placeholder)</h2>
        <p className="text-[var(--foreground)]">
          Tools for building and analyzing options strategies, including risk profiles and scenario analysis, will be featured here.
        </p>
      </section>
    </div>
  );
};

export default OptionsPage;
