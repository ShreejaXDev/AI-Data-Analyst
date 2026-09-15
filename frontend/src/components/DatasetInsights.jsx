import React, { useState } from 'react';
import { Database, Columns, AlertTriangle, Copy, FileSpreadsheet, ChevronDown, ChevronUp } from 'lucide-react';
import { formatNumber, getTypeBadgeColor } from '../utils/formatters';
import DataPreviewTable from './DataPreviewTable';

export default function DatasetInsights({ dataset }) {
  const [showColumns, setShowColumns] = useState(true);

  if (!dataset) return null;

  const totalMissing = Object.values(dataset.missing_values || {}).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-4 overflow-y-auto max-h-full pr-1">
      {/* 4 Stat Cards */}
      <div className="grid grid-cols-2 gap-3.5">
        {/* Rows Card */}
        <div className="p-4 rounded-2xl card-blue shadow-sm space-y-1.5 transition hover:shadow-md">
          <div className="flex items-center justify-between text-slate-700 text-xs sm:text-sm font-bold">
            <span>Rows</span>
            <div className="p-1.5 rounded-lg bg-blue-100">
              <Database className="h-4 sm:h-5 w-4 sm:w-5 text-blue-600" />
            </div>
          </div>
          <p className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">{formatNumber(dataset.rows)}</p>
        </div>

        {/* Columns Card */}
        <div className="p-4 rounded-2xl card-violet shadow-sm space-y-1.5 transition hover:shadow-md">
          <div className="flex items-center justify-between text-slate-700 text-xs sm:text-sm font-bold">
            <span>Columns</span>
            <div className="p-1.5 rounded-lg bg-violet-100">
              <Columns className="h-4 sm:h-5 w-4 sm:w-5 text-violet-600" />
            </div>
          </div>
          <p className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">{dataset.columns}</p>
        </div>

        {/* Missing Values Card */}
        <div className={`p-4 rounded-2xl ${totalMissing > 0 ? 'card-amber' : 'card-emerald'} shadow-sm space-y-1.5 transition hover:shadow-md`}>
          <div className="flex items-center justify-between text-slate-700 text-xs sm:text-sm font-bold">
            <span>Missing</span>
            <div className={`p-1.5 rounded-lg ${totalMissing > 0 ? 'bg-amber-100' : 'bg-emerald-100'}`}>
              <AlertTriangle className={`h-4 sm:h-5 w-4 sm:w-5 ${totalMissing > 0 ? 'text-amber-600' : 'text-emerald-600'}`} />
            </div>
          </div>
          <p className={`text-2xl sm:text-3xl font-black ${totalMissing > 0 ? 'text-amber-800' : 'text-slate-900'} tracking-tight`}>
            {formatNumber(totalMissing)}
          </p>
        </div>

        {/* Duplicate Rows Card */}
        <div className={`p-4 rounded-2xl ${dataset.duplicate_rows > 0 ? 'card-rose' : 'card-emerald'} shadow-sm space-y-1.5 transition hover:shadow-md`}>
          <div className="flex items-center justify-between text-slate-700 text-xs sm:text-sm font-bold">
            <span>Duplicates</span>
            <div className={`p-1.5 rounded-lg ${dataset.duplicate_rows > 0 ? 'bg-rose-100' : 'bg-emerald-100'}`}>
              <Copy className={`h-4 sm:h-5 w-4 sm:w-5 ${dataset.duplicate_rows > 0 ? 'text-rose-600' : 'text-emerald-600'}`} />
            </div>
          </div>
          <p className={`text-2xl sm:text-3xl font-black ${dataset.duplicate_rows > 0 ? 'text-rose-800' : 'text-slate-900'} tracking-tight`}>
            {dataset.duplicate_rows}
          </p>
        </div>
      </div>

      {/* Column Schema Accordion */}
      <div className="bg-white rounded-2xl border-2 border-indigo-200/80 shadow-md overflow-hidden">
        <button
          onClick={() => setShowColumns(!showColumns)}
          className="w-full px-4 py-3 bg-gradient-to-r from-slate-900 to-indigo-950 border-b border-indigo-200/60 flex items-center justify-between text-xs sm:text-sm font-extrabold text-white text-left shadow-xs"
        >
          <div className="flex items-center gap-2.5">
            <FileSpreadsheet className="h-4 sm:h-5 w-4 sm:w-5 text-indigo-400" />
            <span>Column Schema & Data Types ({dataset.column_names?.length})</span>
          </div>
          {showColumns ? <ChevronUp className="h-5 w-5 text-slate-300" /> : <ChevronDown className="h-5 w-5 text-slate-300" />}
        </button>

        {showColumns && (
          <div className="p-3.5 max-h-[240px] overflow-y-auto space-y-2 divide-y divide-slate-100 bg-white">
            {dataset.column_names?.map((col, idx) => {
              const dtype = dataset.dtypes?.[col] || 'unknown';
              const missingCount = dataset.missing_values?.[col] || 0;
              return (
                <div key={idx} className="pt-2 first:pt-0 flex items-center justify-between text-xs sm:text-sm">
                  <span className="font-bold text-slate-800 truncate max-w-[150px]" title={col}>
                    {col}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className={`px-2.5 py-0.5 rounded-full border text-xs font-mono font-bold shadow-2xs ${getTypeBadgeColor(dtype)}`}>
                      {dtype}
                    </span>
                    {missingCount > 0 && (
                      <span className="px-2 py-0.5 rounded-md bg-amber-100 text-amber-900 text-xs font-mono font-extrabold border border-amber-300 shadow-2xs">
                        {missingCount} null
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Raw Sample Data Preview */}
      <DataPreviewTable preview={dataset.preview} columnNames={dataset.column_names} dtypes={dataset.dtypes} />
    </div>
  );
}
