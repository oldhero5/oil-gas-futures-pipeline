// frontend/src/components/futures/HistoricalFuturesChart.tsx
'use client';

import React, { useState, ChangeEvent } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

// Mock historical data structure
interface HistoricalPricePoint {
  date: string; // YYYY-MM-DD
  price: number;
}

interface HistoricalContractData {
  contractName: string;
  prices: HistoricalPricePoint[];
}

const generateThirtyDayData = (startDate: string, startPrice: number, volatility: number): HistoricalPricePoint[] => {
  const data: HistoricalPricePoint[] = [];
  const currentDate = new Date(startDate);
  let currentPrice = startPrice;
  for (let i = 0; i < 30; i++) {
    data.push({
      date: currentDate.toISOString().split('T')[0],
      price: parseFloat(currentPrice.toFixed(2)),
    });
    currentDate.setDate(currentDate.getDate() + 1);
    const change = (Math.random() - 0.48) * volatility;
    currentPrice += change;
    if (currentPrice < 0) currentPrice = 0.01;
  }
  return data;
};

const mockHistoricalData: HistoricalContractData[] = [
  {
    contractName: 'Crude Oil WTI (CL)',
    prices: generateThirtyDayData('2025-04-27', 78.50, 0.8),
  },
  {
    contractName: 'Natural Gas (NG)',
    prices: generateThirtyDayData('2025-04-27', 2.50, 0.1),
  },
];

const HistoricalFuturesChart: React.FC = () => {
  const [selectedContractName, setSelectedContractName] = useState<string>(mockHistoricalData[0].contractName);

  const selectedContractData = mockHistoricalData.find(contract => contract.contractName === selectedContractName) || mockHistoricalData[0];

  const handleContractChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setSelectedContractName(event.target.value);
  };

  return (
    <div className="bg-[var(--secondary-background)] p-6 rounded-lg shadow-xl text-[var(--foreground)] mt-8">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-semibold text-[var(--accent)]">
          Historical Prices: {selectedContractData.contractName}
        </h3>
        <div>
          <label htmlFor="contract-select" className="mr-2 text-sm text-[var(--muted-foreground)]">Select Contract:</label>
          <select
            id="contract-select"
            value={selectedContractName}
            onChange={handleContractChange}
            className="bg-[var(--background)] border border-[var(--border-color)] text-[var(--foreground)] text-sm rounded-lg focus:ring-[var(--accent)] focus:border-[var(--accent)] p-2"
          >
            {mockHistoricalData.map(contract => (
              <option key={contract.contractName} value={contract.contractName}>
                {contract.contractName}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div style={{ width: '100%', height: 400 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={selectedContractData.prices}
            margin={{
              top: 5,
              right: 30,
              left: 20,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
            <XAxis
                dataKey="date"
                stroke="var(--muted-foreground)"
                tickFormatter={(tick) => new Date(tick).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            />
            <YAxis stroke="var(--muted-foreground)" domain={['auto', 'auto']} />
            <Tooltip
                contentStyle={{ backgroundColor: 'var(--background)', border: '1px solid var(--border-color)' }}
                labelStyle={{ color: 'var(--accent)' }}
            />
            <Legend wrapperStyle={{ color: 'var(--foreground)' }}/>
            <Line
                type="monotone"
                dataKey="price"
                stroke="var(--accent)"
                strokeWidth={2}
                activeDot={{ r: 8 }}
                dot={{ r: 3 }}
                name={selectedContractData.contractName}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default HistoricalFuturesChart;
