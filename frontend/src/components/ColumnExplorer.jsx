import React, { useState, useMemo } from 'react';
import { Search, Hash, Tag, AlertTriangle, Layers, BarChart2 } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { getTypeBadgeColor } from '../utils/formatters';

export default function ColumnExplorer({ dataset }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeFilter, setActiveFilter] = useState('ALL');

  if (!dataset || !dataset.column_names) return null;

  const totalRows = dataset.rows || 1;
  const preview = dataset.preview || [];

  // Filter columns based on search term & filter chip
  const filteredColumns = useMemo(() => {
    return dataset.column_names.filter((col) => {
      const dtype = (dataset.dtypes?.[col] || '').toLowerCase();
      const isNumeric = dtype.includes('int') || dtype.includes('float') || dtype.includes('number');
      const missingCount = dataset.missing_values?.[col] || 0;

      // Filter category check
      if (activeFilter === 'NUMERIC' && !isNumeric) return false;
      if (activeFilter === 'CATEGORICAL' && isNumeric) return false;
      if (activeFilter === 'MISSING' && missingCount === 0) return false;

      // Search term check
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase();
        return col.toLowerCase().includes(query) || dtype.includes(query);
      }

      return true;
    });
  }, [dataset, searchTerm, activeFilter]);

  // Compute column distribution data from preview for Recharts
  const getColumnChartData = (col, isNumeric) => {
    if (!preview || preview.length === 0) return [];

    if (isNumeric) {
      return preview.slice(0, 10).map((row, idx) => ({
        name: `R${idx + 1}`,
        val: typeof row[col] === 'number' ? row[col] : 0,
      }));
    } else {
      const counts = {};
      preview.forEach((row) => {
        const val = row[col] !== null && row[col] !== undefined ? String(row[col]) : 'null';
        counts[val] = (counts[val] || 0) + 1;
      });
      return Object.entries(counts).map(([name, val]) => ({
        name: name.length > 10 ? `${name.substring(0, 8)}...` : name,
        val,
      }));
    }
  };

  const BAR_COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#06b6d4', '#10b981', '#f59e0b'];

  return (
    <div className="space-y-4 h-full flex flex-col">
      {/* Header Controls: Search & Filter Chips */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 glass-panel p-4 rounded-2xl border-2 border-indigo-200/80 shadow-md">
        {/* Search Input */}
        <div className="relative w-full sm:w-96">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-5 w-5 text-indigo-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search columns or data types..."
            className="w-full bg-white border-2 border-slate-200 focus:border-indigo-600 rounded-xl pl-11 pr-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition shadow-xs font-medium"
          />
        </div>

        {/* Filter Chips */}
        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
          {[
            { id: 'ALL', label: 'All Columns', icon: Layers, activeClass: 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30' },
            { id: 'NUMERIC', label: 'Numeric', icon: Hash, activeClass: 'bg-blue-600 text-white shadow-md shadow-blue-600/30' },
            { id: 'CATEGORICAL', label: 'Categorical', icon: Tag, activeClass: 'bg-violet-600 text-white shadow-md shadow-violet-600/30' },
            { id: 'MISSING', label: 'Has Missing', icon: AlertTriangle, activeClass: 'bg-amber-600 text-white shadow-md shadow-amber-600/30' },
          ].map((chip) => {
            const Icon = chip.icon;
            const isActive = activeFilter === chip.id;
            return (
              <button
                key={chip.id}
                onClick={() => setActiveFilter(chip.id)}
                className={`px-3.5 py-2 rounded-xl text-xs sm:text-sm font-bold flex items-center gap-2 transition whitespace-nowrap ${
                  isActive
                    ? chip.activeClass
                    : 'bg-white text-slate-700 hover:text-slate-900 border border-slate-300 hover:border-indigo-400 shadow-xs'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{chip.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Columns Grid */}
      <div className="flex-1 overflow-y-auto pr-1 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredColumns.length === 0 ? (
          <div className="col-span-full text-center py-16 glass-panel rounded-2xl border-2 border-slate-200 text-slate-600 text-sm font-semibold">
            No columns match your search filter.
          </div>
        ) : (
          filteredColumns.map((col, idx) => {
            const dtype = dataset.dtypes?.[col] || 'unknown';
            const typeStr = String(dtype).toLowerCase();
            const isNumeric = typeStr.includes('int') || typeStr.includes('float') || typeStr.includes('number');
            const missingCount = dataset.missing_values?.[col] || 0;
            const missingPct = ((missingCount / totalRows) * 100).toFixed(1);

            // Extract sample values from preview
            const samples = preview
              .map((row) => row[col])
              .filter((val) => val !== null && val !== undefined)
              .slice(0, 4);

            const chartData = getColumnChartData(col, isNumeric);
            const cardTheme = isNumeric ? 'card-indigo' : 'card-violet';

            return (
              <div
                key={idx}
                className={`p-4 rounded-2xl ${cardTheme} shadow-sm space-y-3 flex flex-col justify-between hover:shadow-lg transition-all group border-2`}
              >
                {/* Column Header */}
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="font-extrabold text-slate-900 text-base sm:text-lg truncate max-w-[180px]" title={col}>
                      {col}
                    </h3>
                    <span className={`px-3 py-1 rounded-full border text-xs font-mono font-bold shadow-2xs ${getTypeBadgeColor(dtype)}`}>
                      {dtype}
                    </span>
                  </div>

                  {/* Missing Values Progress Bar */}
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs font-bold text-slate-600">
                      <span>Missing Data</span>
                      <span className={missingCount > 0 ? 'text-amber-700 font-extrabold' : 'text-emerald-700 font-extrabold'}>
                        {missingCount} ({missingPct}%)
                      </span>
                    </div>
                    <div className="w-full h-2 bg-slate-200/80 rounded-full overflow-hidden shadow-inner">
                      <div
                        className={`h-full transition-all duration-300 ${missingCount > 0 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                        style={{ width: `${Math.max(Number(missingPct), 2)}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Sample Values Chips */}
                <div className="space-y-1.5">
                  <p className="text-xs font-extrabold text-slate-500 uppercase tracking-wider">Sample Values</p>
                  <div className="flex flex-wrap gap-1.5">
                    {samples.map((s, sIdx) => (
                      <span
                        key={sIdx}
                        className="px-2.5 py-1 rounded-lg bg-white border border-slate-300 text-slate-800 font-mono text-xs font-semibold shadow-2xs truncate max-w-[130px]"
                      >
                        {String(s)}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Mini Recharts Distribution Preview */}
                {chartData.length > 0 && (
                  <div className="pt-3 border-t border-indigo-100 space-y-1.5">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-700">
                      <BarChart2 className="h-4 w-4 text-indigo-600" />
                      <span>{isNumeric ? 'Value Distribution Trend' : 'Top Categories'}</span>
                    </div>
                    <div className="h-28 w-full bg-white rounded-xl p-2 border border-indigo-200 shadow-2xs">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                          <XAxis dataKey="name" stroke="#475569" fontSize={10} fontWeight={600} tickLine={false} />
                          <YAxis stroke="#475569" fontSize={10} fontWeight={600} tickLine={false} />
                          <Tooltip
                            contentStyle={{ background: '#ffffff', borderColor: '#818cf8', borderRadius: '10px', fontSize: '12px', fontWeight: 600, boxShadow: '0 8px 16px -2px rgba(99,102,241,0.2)' }}
                            itemStyle={{ color: '#4338ca' }}
                          />
                          <Bar dataKey="val" radius={[6, 6, 0, 0]}>
                            {chartData.map((_, index) => (
                              <Cell key={`cell-${index}`} fill={BAR_COLORS[index % BAR_COLORS.length]} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
