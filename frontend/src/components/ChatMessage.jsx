import React, { useState } from 'react';
import { User, Bot, BarChart2, Maximize2, X, Download, Copy, Check, RotateCcw, AlertTriangle } from 'lucide-react';
import { getFullChartUrl } from '../services/api';
import AgentActivity from './AgentActivity';

export default function ChatMessage({ message, onRetry }) {
  const isUser = message.sender === 'user';
  const [showModal, setShowModal] = useState(false);
  const [copied, setCopied] = useState(false);

  const chartUrl = message.chart ? getFullChartUrl(message.chart) : null;

  const handleCopy = () => {
    navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Parse Markdown Tables
  const parseMarkdownTable = (lines) => {
    const tableRows = lines.map((line) =>
      line
        .split('|')
        .map((cell) => cell.trim())
        .filter((cell, idx, arr) => idx > 0 && idx < arr.length - 1)
    );

    if (tableRows.length < 2) return null;

    const headers = tableRows[0];
    const contentRows = tableRows.slice(1).filter(
      (row) => !row.every((cell) => cell.includes('---') || cell === '')
    );

    return (
      <div className="overflow-x-auto my-3 rounded-2xl border-2 border-indigo-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm border-collapse">
          <thead className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 border-b-2 border-indigo-400 text-white">
            <tr>
              {headers.map((h, i) => (
                <th key={i} className="px-4 py-3 font-extrabold text-white text-xs uppercase tracking-wider whitespace-nowrap">
                  {formatBold(h)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {contentRows.map((row, rIdx) => (
              <tr key={rIdx} className="odd:bg-white even:bg-indigo-50/20 hover:bg-indigo-100/60 transition">
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="px-4 py-3 text-slate-800 font-semibold whitespace-nowrap">
                    {formatBold(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // Formatter for Analyst Report text
  const renderFormattedText = (text) => {
    if (!text) return null;

    const lines = text.split('\n');
    const elements = [];
    let tableBuffer = [];
    let keyCounter = 0;

    const flushTable = () => {
      if (tableBuffer.length > 0) {
        const parsedTable = parseMarkdownTable(tableBuffer);
        if (parsedTable) {
          elements.push(<React.Fragment key={`tbl-${keyCounter++}`}>{parsedTable}</React.Fragment>);
        } else {
          tableBuffer.forEach((line) => {
            elements.push(<p key={`txt-${keyCounter++}`} className="text-base text-slate-800 my-1 font-medium">{formatBold(line)}</p>);
          });
        }
        tableBuffer = [];
      }
    };

    lines.forEach((line) => {
      const trimmed = line.trim();

      // Table line detection
      if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
        tableBuffer.push(trimmed);
        return;
      } else {
        flushTable();
      }

      if (!trimmed) {
        elements.push(<div key={`sp-${keyCounter++}`} className="h-2" />);
        return;
      }

      // Headers (### or ## or #)
      if (trimmed.startsWith('### ')) {
        elements.push(
          <h4 key={`h3-${keyCounter++}`} className="text-base font-extrabold text-indigo-700 mt-4 mb-1.5">
            {trimmed.substring(4)}
          </h4>
        );
        return;
      }
      if (trimmed.startsWith('## ')) {
        elements.push(
          <h3 key={`h2-${keyCounter++}`} className="text-lg font-black text-slate-900 mt-5 mb-2 border-b-2 border-indigo-200 pb-1">
            {trimmed.substring(3)}
          </h3>
        );
        return;
      }

      // Bullet lists (* or -)
      if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
        elements.push(
          <li key={`li-${keyCounter++}`} className="ml-5 list-disc text-base text-slate-800 my-1 font-medium leading-relaxed">
            {formatBold(trimmed.substring(2))}
          </li>
        );
        return;
      }

      // Numbered lists (1. , 2. )
      if (/^\d+\.\s/.test(trimmed)) {
        const match = trimmed.match(/^(\d+\.)\s*(.*)/);
        if (match) {
          elements.push(
            <div key={`num-${keyCounter++}`} className="flex gap-2.5 text-base text-slate-800 my-1 font-medium">
              <span className="font-bold text-indigo-700 font-mono">{match[1]}</span>
              <span>{formatBold(match[2])}</span>
            </div>
          );
          return;
        }
      }

      // Normal paragraph
      elements.push(
        <p key={`p-${keyCounter++}`} className="text-base text-slate-800 my-1.5 leading-relaxed font-normal">
          {formatBold(trimmed)}
        </p>
      );
    });

    flushTable();
    return elements;
  };

  const formatBold = (str) => {
    if (!str) return '';
    const parts = str.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, idx) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={idx} className="font-extrabold text-slate-950">{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  return (
    <div className={`flex gap-3.5 my-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* AI Avatar */}
      {!isUser && (
        <div className="h-9 w-9 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 shrink-0 mt-1">
          <Bot className="h-5 w-5" />
        </div>
      )}

      <div className={`max-w-[88%] sm:max-w-[82%] space-y-2.5 ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Error State Card */}
        {message.isError ? (
          <div className="p-4.5 rounded-2xl bg-rose-50 border-2 border-rose-300 text-slate-900 space-y-3 shadow-sm">
            <div className="flex items-center gap-2.5 text-rose-800 font-bold text-sm sm:text-base">
              <AlertTriangle className="h-5 w-5 shrink-0 text-rose-600" />
              <span>Something went wrong while analyzing your dataset.</span>
            </div>

            {onRetry && (
              <button
                onClick={() => onRetry(message.originalQuestion)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs sm:text-sm font-bold transition shadow-md shadow-rose-600/25"
              >
                <RotateCcw className="h-4 w-4" />
                <span>Retry Analysis</span>
              </button>
            )}
          </div>
        ) : (
          /* Normal Message Card */
          <div
            className={`p-4.5 sm:p-5 rounded-2xl shadow-md relative group ${
              isUser
                ? 'bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-700 text-white rounded-tr-none text-base font-semibold shadow-indigo-600/25'
                : 'bg-white border-2 border-indigo-200/90 text-slate-800 rounded-tl-none shadow-sm'
            }`}
          >
            {/* Formatted Report Text */}
            <div className="space-y-1.5">{renderFormattedText(message.text)}</div>

            {/* Copy Action for AI */}
            {!isUser && (
              <button
                onClick={handleCopy}
                className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 p-2 rounded-xl bg-slate-100 hover:bg-indigo-50 text-slate-600 hover:text-indigo-700 transition text-xs flex items-center gap-1.5 border border-slate-300 shadow-xs font-bold"
                title="Copy answer"
              >
                {copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
              </button>
            )}
          </div>
        )}

        {/* Action Steps History (if available) */}
        {!isUser && message.actions && message.actions.length > 0 && (
          <AgentActivity isWorking={false} actions={message.actions} />
        )}

        {/* Generated Visualization Chart Card */}
        {chartUrl && (
          <div className="mt-3.5 p-4 rounded-2xl bg-white border-2 border-indigo-200 max-w-lg space-y-2.5 shadow-md">
            <div className="flex items-center justify-between text-xs sm:text-sm text-slate-800 font-extrabold px-1">
              <span className="flex items-center gap-2 text-indigo-700">
                <BarChart2 className="h-5 w-5 text-indigo-600" />
                Generated Visualization Chart
              </span>
              <button
                onClick={() => setShowModal(true)}
                className="p-1.5 rounded-lg hover:bg-indigo-50 text-slate-600 hover:text-indigo-700 transition"
                title="Expand chart"
              >
                <Maximize2 className="h-4 w-4" />
              </button>
            </div>

            <div
              onClick={() => setShowModal(true)}
              className="cursor-pointer overflow-hidden rounded-xl border-2 border-slate-200 bg-slate-50 hover:border-indigo-500 transition group relative shadow-xs"
            >
              <img
                src={chartUrl}
                alt="AI Generated Chart"
                className="w-full h-auto object-contain max-h-[300px] group-hover:scale-[1.02] transition-transform duration-300"
              />
              <div className="absolute inset-0 bg-indigo-900/15 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <span className="text-xs sm:text-sm font-extrabold text-slate-900 px-4 py-2 rounded-xl bg-white border border-indigo-300 shadow-lg">
                  Click to Expand Chart
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Message Timestamp */}
        {message.timestamp && (
          <div className={`text-[10px] text-slate-400 font-mono px-1 font-medium ${isUser ? 'text-right' : 'text-left'}`}>
            {message.timestamp}
          </div>
        )}
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="h-8 w-8 rounded-xl bg-slate-200 border border-slate-300 flex items-center justify-center text-slate-700 shrink-0 mt-1 shadow-xs">
          <User className="h-4 w-4" />
        </div>
      )}

      {/* Fullscreen Chart Modal */}
      {showModal && chartUrl && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="relative max-w-4xl w-full bg-white p-4 rounded-2xl border border-slate-200 shadow-2xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <BarChart2 className="h-4 w-4 text-indigo-600" />
                Visualization Preview
              </h3>
              <div className="flex items-center gap-2">
                <a
                  href={chartUrl}
                  download="chart.png"
                  target="_blank"
                  rel="noreferrer"
                  className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold flex items-center gap-1 border border-slate-200"
                >
                  <Download className="h-3.5 w-3.5" />
                  Download
                </a>
                <button
                  onClick={() => setShowModal(false)}
                  className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
            <div className="flex items-center justify-center bg-slate-50 rounded-xl p-2 border border-slate-200">
              <img src={chartUrl} alt="Chart Fullscreen" className="max-h-[75vh] w-auto object-contain" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
