import React from 'react';
import { Database, Columns, AlertTriangle, Copy, Hash, Tag } from 'lucide-react';
import { formatNumber } from '../utils/formatters';

export default function DatasetOverview({ dataset }) {
  if (!dataset) return null;

  const totalMissing = Object.values(dataset.missing_values || {}).reduce((a, b) => a + b, 0);

  // Compute numeric vs categorical column counts
  const dtypes = dataset.dtypes || {};
  let numericCount = 0;
  let categoricalCount = 0;

  Object.values(dtypes).forEach((dtype) => {
    const typeStr = String(dtype).toLowerCase();
    if (typeStr.includes('int') || typeStr.includes('float') || typeStr.includes('number')) {
      numericCount++;
    } else {
      categoricalCount++;
    }
  });

  const cards = [
    {
      label: 'Total Rows',
      value: formatNumber(dataset.rows),
      icon: Database,
      cardClass: 'card-blue',
      color: 'text-blue-600',
      bg: 'bg-blue-100',
    },
    {
      label: 'Total Columns',
      value: dataset.columns,
      icon: Columns,
      cardClass: 'card-violet',
      color: 'text-violet-600',
      bg: 'bg-violet-100',
    },
    {
      label: 'Missing Values',
      value: formatNumber(totalMissing),
      icon: AlertTriangle,
      cardClass: totalMissing > 0 ? 'card-amber' : 'card-emerald',
      color: totalMissing > 0 ? 'text-amber-600' : 'text-emerald-600',
      bg: totalMissing > 0 ? 'bg-amber-100' : 'bg-emerald-100',
    },
    {
      label: 'Duplicate Rows',
      value: dataset.duplicate_rows,
      icon: Copy,
      cardClass: dataset.duplicate_rows > 0 ? 'card-rose' : 'card-emerald',
      color: dataset.duplicate_rows > 0 ? 'text-rose-600' : 'text-emerald-600',
      bg: dataset.duplicate_rows > 0 ? 'bg-rose-100' : 'bg-emerald-100',
    },
    {
      label: 'Numeric Columns',
      value: numericCount,
      icon: Hash,
      cardClass: 'card-emerald',
      color: 'text-emerald-600',
      bg: 'bg-emerald-100',
    },
    {
      label: 'Categorical Columns',
      value: categoricalCount,
      icon: Tag,
      cardClass: 'card-indigo',
      color: 'text-indigo-600',
      bg: 'bg-indigo-100',
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 mb-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`p-4 rounded-2xl ${card.cardClass} shadow-sm space-y-2.5 transition-all duration-200 transform hover:-translate-y-0.5`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs sm:text-sm text-slate-700 font-bold truncate">{card.label}</span>
              <div className={`p-2 rounded-xl ${card.bg} shadow-xs`}>
                <Icon className={`h-4 sm:h-5 w-4 sm:w-5 ${card.color}`} />
              </div>
            </div>
            <p className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
              {card.value}
            </p>
          </div>
        );
      })}
    </div>
  );
}
