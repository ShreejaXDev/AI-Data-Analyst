import React, { useState, useMemo } from 'react';
import { Table, Search, ChevronLeft, ChevronRight, Hash, Tag } from 'lucide-react';
import { getTypeBadgeColor } from '../utils/formatters';

export default function DataPreviewTable({ preview = [], columnNames = [], dtypes = {} }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(5);

  if (!preview || preview.length === 0) {
    return (
      <div className="p-8 text-center glass-panel rounded-2xl border border-slate-200 text-slate-500 text-xs">
        No dataset rows available to display.
      </div>
    );
  }

  const columns = columnNames.length > 0 ? columnNames : Object.keys(preview[0] || {});

  // Search filter across row cells
  const filteredRows = useMemo(() => {
    if (!searchTerm.trim()) return preview;
    const query = searchTerm.toLowerCase();

    return preview.filter((row) =>
      columns.some((col) => {
        const val = row[col];
        return val !== null && val !== undefined && String(val).toLowerCase().includes(query);
      })
    );
  }, [preview, columns, searchTerm]);

  // Pagination calculation
  const totalRows = filteredRows.length;
  const totalPages = Math.ceil(totalRows / pageSize) || 1;
  const startIndex = (currentPage - 1) * pageSize;
  const paginatedRows = filteredRows.slice(startIndex, startIndex + pageSize);

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  return (
    <div className="bg-white rounded-2xl border-2 border-indigo-200/80 overflow-hidden flex flex-col h-full shadow-md">
      {/* Table Header Controls */}
      <div className="p-4 bg-slate-50 border-b-2 border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 text-sm font-extrabold text-slate-900">
          <Table className="h-5 w-5 text-indigo-600" />
          <span>Interactive Dataset Preview ({totalRows} rows)</span>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          {/* Search Row Filter */}
          <div className="relative flex-1 sm:w-72">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-indigo-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Filter row values..."
              className="w-full bg-white border border-slate-300 focus:border-indigo-600 rounded-xl pl-10 pr-3 py-2 text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition shadow-xs font-medium"
            />
          </div>

          {/* Rows Per Page Selector */}
          <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-700 font-bold">
            <span>Show:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="bg-white border border-slate-300 rounded-xl px-3 py-1.5 text-xs sm:text-sm text-slate-900 font-bold focus:outline-none focus:border-indigo-600 shadow-xs"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={25}>25</option>
            </select>
          </div>
        </div>
      </div>

      {/* Scrollable Data Table Container */}
      <div className="flex-1 overflow-auto max-h-[520px]">
        <table className="w-full text-left border-collapse text-sm">
          <thead className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 sticky top-0 border-b-2 border-indigo-400 z-10 shadow-sm text-white">
            <tr>
              <th className="px-4 py-3 font-mono text-xs uppercase w-12 text-slate-300">#</th>
              {columns.map((col, idx) => {
                const dtype = dtypes[col] || '';
                const isNumeric = dtype.includes('int') || dtype.includes('float') || dtype.includes('number');
                return (
                  <th
                    key={idx}
                    className={`px-4 py-3 font-bold text-xs uppercase tracking-wider text-slate-100 whitespace-nowrap ${
                      isNumeric ? 'text-right' : 'text-left'
                    }`}
                  >
                    <div className={`flex items-center gap-1.5 ${isNumeric ? 'justify-end' : 'justify-start'}`}>
                      {isNumeric ? <Hash className="h-4 w-4 text-emerald-400" /> : <Tag className="h-4 w-4 text-sky-400" />}
                      <span className="font-extrabold text-white text-sm">{col}</span>
                      {dtype && (
                        <span className={`ml-1 text-[10px] font-mono px-2 py-0.5 rounded-full border shadow-2xs ${getTypeBadgeColor(dtype)}`}>
                          {dtype}
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {paginatedRows.length === 0 ? (
              <tr>
                <td colSpan={columns.length + 1} className="text-center py-12 text-slate-600 text-sm font-semibold">
                  No matching row values found for "{searchTerm}".
                </td>
              </tr>
            ) : (
              paginatedRows.map((row, rIdx) => (
                <tr key={rIdx} className="odd:bg-white even:bg-indigo-50/20 hover:bg-indigo-100/60 transition">
                  <td className="px-4 py-3 text-slate-500 font-mono text-xs font-bold">{startIndex + rIdx + 1}</td>
                  {columns.map((col, cIdx) => {
                    const val = row[col];
                    const dtype = dtypes[col] || '';
                    const isNumeric = typeof val === 'number' || dtype.includes('int') || dtype.includes('float');
                    const isNull = val === null || val === undefined || val === '';

                    return (
                      <td
                        key={cIdx}
                        className={`px-4 py-3 whitespace-nowrap max-w-[260px] truncate text-sm ${
                          isNumeric ? 'text-right font-mono text-slate-900 font-bold' : 'text-left text-slate-800 font-semibold'
                        }`}
                      >
                        {isNull ? (
                          <span className="px-2.5 py-1 rounded-md bg-amber-100 text-amber-900 font-mono text-xs font-extrabold border border-amber-300 shadow-2xs">
                            N/A
                          </span>
                        ) : (
                          String(val)
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls Footer */}
      <div className="p-4 bg-slate-50 border-t-2 border-slate-200 flex items-center justify-between text-xs sm:text-sm text-slate-700 font-bold">
        <div>
          Showing <span className="font-extrabold text-indigo-700">{startIndex + 1}</span> to{' '}
          <span className="font-extrabold text-indigo-700">{Math.min(startIndex + pageSize, totalRows)}</span> of{' '}
          <span className="font-extrabold text-indigo-700">{totalRows}</span> rows
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="p-2 rounded-xl bg-white border border-slate-300 hover:border-indigo-500 hover:bg-indigo-50 disabled:opacity-40 disabled:cursor-not-allowed text-slate-800 transition shadow-xs"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <span className="text-xs sm:text-sm font-mono font-bold text-slate-800 px-2 py-1 rounded-lg bg-white border border-slate-200">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="p-2 rounded-xl bg-white border border-slate-300 hover:border-indigo-500 hover:bg-indigo-50 disabled:opacity-40 disabled:cursor-not-allowed text-slate-800 transition shadow-xs"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
