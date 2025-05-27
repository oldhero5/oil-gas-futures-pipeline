// frontend/src/app/futures/page.tsx
'use client';

import React from 'react';
import FuturesPriceGrid from '@/components/dashboard/FuturesPriceGrid'; // Reverted to original path
import HistoricalFuturesChart from '@/components/futures/HistoricalFuturesChart'; // Import the new chart component

const FuturesPage: React.FC = () => {
  return (
    <div className="container mx-auto p-4 md:p-6 text-[var(--foreground)]">
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-[var(--accent)]">Futures Market Overview</h1>
        <p className="text-lg text-[var(--muted-foreground)] mt-2">
          Track real-time and historical futures contract prices across various commodities.
        </p>
      </header>

      {/* Current Prices Grid */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold text-[var(--accent)] mb-4">Current Contract Prices</h2>
        <FuturesPriceGrid />
      </section>

      {/* Historical Price Chart Section */}
      <section>
        <h2 className="text-2xl font-semibold text-[var(--accent)] mb-4">Historical Price Analysis</h2>
        <HistoricalFuturesChart />
      </section>

      {/* Placeholder for future charts or additional info */}
      <section className="bg-[var(--secondary-background)] p-6 rounded-lg shadow-xl">
        <h2 className="text-2xl font-semibold text-[var(--accent)] mb-4">Market Trends & Analysis (Placeholder)</h2>
        <p className="text-[var(--foreground)]">
          Detailed charts and analytical tools for futures contracts will be displayed here.
          This section will provide insights into price trends, volatility, and other key market indicators.
        </p>
      </section>
    </div>
  );
};

export default FuturesPage;
