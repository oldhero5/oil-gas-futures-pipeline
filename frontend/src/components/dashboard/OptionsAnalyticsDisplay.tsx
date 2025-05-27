// frontend/src/components/dashboard/OptionsAnalyticsDisplay.tsx
'use client';

import React from 'react';

interface OptionContract {
  id: string;
  underlying: string;
  type: 'Call' | 'Put';
  strikePrice: number;
  premium: number;
  expiryDate: string;
  impliedVolatility: number;
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
}

const mockOptionsData: OptionContract[] = [
  {
    id: 'CLF24C80',
    underlying: 'CLF24',
    type: 'Call',
    strikePrice: 80.00,
    premium: 2.50,
    expiryDate: '2024-01-20',
    impliedVolatility: 35.5,
    delta: 0.45,
    gamma: 0.05,
    theta: -0.02,
    vega: 0.10,
  },
  {
    id: 'CLF24P70',
    underlying: 'CLF24',
    type: 'Put',
    strikePrice: 70.00,
    premium: 1.80,
    expiryDate: '2024-01-20',
    impliedVolatility: 33.2,
    delta: -0.35,
    gamma: 0.04,
    theta: -0.018,
    vega: 0.09,
  },
  {
    id: 'NGG24C3.0',
    underlying: 'NGG24',
    type: 'Call',
    strikePrice: 3.00,
    premium: 0.15,
    expiryDate: '2024-02-28',
    impliedVolatility: 45.0,
    delta: 0.52,
    gamma: 0.12,
    theta: -0.005,
    vega: 0.02,
  },
];

const OptionsAnalyticsDisplay: React.FC = () => {
  return (
    <div className="bg-[var(--secondary-background)] p-6 rounded-lg shadow-xl text-[var(--foreground)]">
      <h2 className="text-2xl font-semibold text-[var(--accent)] mb-6">Options Chain & Analytics</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-[var(--border-color)]">
          <thead className="bg-[var(--background)]">
            <tr>
              {['ID', 'Type', 'Strike', 'Premium', 'Expiry', 'IV', 'Delta', 'Gamma', 'Theta', 'Vega'].map((header) => (
                <th key={header} scope="col" className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-color)]">
            {mockOptionsData.map((option) => (
              <tr key={option.id} className="hover:bg-[var(--background)] transition-colors">
                <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-[var(--accent)]">{option.id}</td>
                <td className={`px-4 py-3 whitespace-nowrap text-sm ${option.type === 'Call' ? 'text-green-400' : 'text-orange-400'}`}>{option.type}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">{option.strikePrice.toFixed(2)}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">{option.premium.toFixed(2)}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">{option.expiryDate}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">{option.impliedVolatility.toFixed(1)}%</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">{option.delta.toFixed(2)}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">{option.gamma.toFixed(2)}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">{option.theta.toFixed(3)}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">{option.vega.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-6 p-4 border border-[var(--border-color)] rounded-md bg-[var(--background)]">
        <h3 className="text-lg font-semibold text-[var(--accent)] mb-2">Analysis Tools (Placeholder)</h3>
        <p className="text-sm">
          Interactive charts for payoff diagrams, volatility smiles, and other options analytics tools will be available here.
        </p>
      </div>
    </div>
  );
};

export default OptionsAnalyticsDisplay;
