import React from 'react';
import { Sparkles, Database, Plus, AlertCircle } from 'lucide-react';
import { formatNumber } from '../utils/formatters';

export default function Header({ dataset, onNewDataset, healthStatus }) {
  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b-2 border-indigo-200/80 px-6 py-4 flex items-center justify-between shadow-md">
      {/* Brand */}
      <div className="flex items-center gap-3.5">
        <div className="h-11 w-11 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
          <Sparkles className="h-6 w-6 text-white animate-pulse" />
        </div>
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl sm:text-2xl font-extrabold tracking-tight bg-gradient-to-r from-slate-900 via-indigo-950 to-purple-900 bg-clip-text text-transparent font-sans">
              AI Data Analyst
            </h1>
            <span className="text-xs uppercase tracking-wider font-bold px-2.5 py-0.5 rounded-full bg-indigo-100 text-indigo-700 border border-indigo-300 shadow-xs">
              Agentic v1.0
            </span>
          </div>
          <p className="text-sm font-medium text-slate-600">Intelligent CSV Analytics & Autonomous Reasoning</p>
        </div>
      </div>

      {/* Dataset & Health Controls */}
      <div className="flex items-center gap-4">
        {/* API Health Status */}
        <div className="hidden sm:flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-emerald-50 border border-emerald-300 text-xs font-bold shadow-xs">
          {healthStatus === 'ok' ? (
            <>
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-600"></span>
              </span>
              <span className="text-emerald-800 font-bold text-xs">API Connected</span>
            </>
          ) : (
            <>
              <AlertCircle className="h-4 w-4 text-amber-500" />
              <span className="text-amber-700 font-bold text-xs">API Connecting...</span>
            </>
          )}
        </div>

        {/* Active Dataset Badge */}
        {dataset && (
          <div className="flex items-center gap-2.5 px-4 py-2 rounded-xl bg-indigo-100/90 border border-indigo-300 text-xs text-indigo-950 font-bold shadow-sm">
            <Database className="h-4 w-4 text-indigo-600" />
            <span className="font-bold truncate max-w-[180px] text-sm">{dataset.filename}</span>
            <span className="text-indigo-700 font-mono text-xs px-2 py-0.5 rounded-md bg-white border border-indigo-200">
              {formatNumber(dataset.rows)} r × {dataset.columns} c
            </span>
          </div>
        )}

        {/* New Dataset Action */}
        {dataset && (
          <button
            onClick={onNewDataset}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white text-xs sm:text-sm font-bold transition shadow-md shadow-indigo-500/25"
          >
            <Plus className="h-4 w-4" />
            <span>New Dataset</span>
          </button>
        )}
      </div>
    </header>
  );
}
