// frontend/src/components/dashboard/FuturesPriceGrid.tsx
'use client';

import React from 'react';

interface FutureContract {
  id: string;
  symbol: string;
  name: string;
  lastPrice: number;
  change: number;
  changePercent: number;
  volume: string;
  openInterest: string;
  expiryDate: string;
}

const mockFuturesData: FutureContract[] = [
  {
    id: 'CLF24',
    symbol: 'CLF24',
    name: 'Crude Oil WTI Futures - Jan 2024',
    lastPrice: 75.50,
    change: -0.25,
    changePercent: -0.33,
    volume: '1.2M',
    openInterest: '500K',
    expiryDate: '2024-01-20',
  },
  {
    id: 'NGG24',
    symbol: 'NGG24',
    name: 'Natural Gas Henry Hub Futures - Feb 2024',
    lastPrice: 2.80,
    change: 0.05,
    changePercent: 1.82,
    volume: '800K',
    openInterest: '300K',
    expiryDate: '2024-02-28',
  },
  {
    id: 'HOZ23',
    symbol: 'HOZ23',
    name: 'Heating Oil Futures - Dec 2023',
    lastPrice: 2.50,
    change: -0.02,
    changePercent: -0.80,
    volume: '450K',
    openInterest: '150K',
    expiryDate: '2023-12-30',
  },
  {
    id: 'RBX23',
    symbol: 'RBX23',
    name: 'RBOB Gasoline Futures - Nov 2023',
    lastPrice: 2.20,
    change: 0.01,
    changePercent: 0.45,
    volume: '600K',
    openInterest: '200K',
    expiryDate: '2023-11-30',
  },
];

const convertToCSV = (data: FutureContract[]): string => {
  if (!data || data.length === 0) {
    return '';
  }
  const headers = ['Symbol', 'Name', 'Last Price', 'Change', '% Change', 'Volume', 'Open Interest', 'Expiry Date'];
  const csvRows = [
    headers.join(','), // header row
    ...data.map(row =>
      [
        `"${row.symbol}"`, // Enclose in quotes to handle potential commas in names
        `"${row.name}"`,
        row.lastPrice.toFixed(2),
        row.change.toFixed(2),
        row.changePercent.toFixed(2),
        `"${row.volume}"`,
        `"${row.openInterest}"`,
        `"${row.expiryDate}"`
      ].join(',')
    )
  ];
  return csvRows.join('\n');
};

const downloadCSV = (csvString: string, filename: string) => {
  const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  if (link.download !== undefined) { // feature detection
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }
};

const FuturesPriceGrid: React.FC = () => {

  const handleExportCSV = () => {
    const csvData = convertToCSV(mockFuturesData);
    const date = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
    downloadCSV(csvData, `futures_prices_${date}.csv`);
  };

  return (
    <div className="bg-[var(--secondary-background)] p-6 rounded-lg shadow-xl text-[var(--foreground)]">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold text-[var(--accent)]">Futures Prices</h2>
        <button
          onClick={handleExportCSV}
          className="bg-[var(--accent)] text-[var(--background)] hover:bg-cyan-500 focus:ring-cyan-300 px-4 py-2 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[var(--secondary-background)] transition-colors"
        >
          Export to CSV
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-[var(--border-color)]">
          <thead className="bg-[var(--background)]">
            <tr>
              {['Symbol', 'Name', 'Last Price', 'Change', '% Change', 'Volume', 'Open Interest', 'Expiry'].map((header) => (
                <th key={header} scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-color)]">
            {mockFuturesData.map((contract) => (
              <tr key={contract.id} className="hover:bg-[var(--background)] transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-[var(--accent)]">{contract.symbol}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">{contract.name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold">{contract.lastPrice.toFixed(2)}</td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm ${contract.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {contract.change.toFixed(2)}
                </td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm ${contract.changePercent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {contract.changePercent.toFixed(2)}%
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">{contract.volume}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">{contract.openInterest}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">{contract.expiryDate}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default FuturesPriceGrid;
