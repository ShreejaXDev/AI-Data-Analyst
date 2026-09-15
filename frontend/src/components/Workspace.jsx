import React, { useState } from 'react';
import { MessageSquare, Search, Table } from 'lucide-react';
import DatasetOverview from './DatasetOverview';
import ChatInterface from './ChatInterface';
import ColumnExplorer from './ColumnExplorer';
import DataPreviewTable from './DataPreviewTable';
import DatasetInsights from './DatasetInsights';

export default function Workspace({
  dataset,
  messages,
  onSendMessage,
  isWorking,
  onClearHistory,
  onRetry
}) {
  const [activeTab, setActiveTab] = useState('CHAT');

  if (!dataset) return null;

  const tabs = [
    { id: 'CHAT', label: 'AI Analyst Chat', icon: MessageSquare },
    { id: 'EXPLORER', label: 'Column Explorer & Schema', icon: Search },
    { id: 'TABLE', label: 'Data Preview Table', icon: Table },
  ];

  return (
    <div className="h-[calc(100vh-65px)] p-4 max-w-7xl mx-auto flex flex-col space-y-3.5">
      {/* 1. Dataset Overview 6 Metric Cards Bar */}
      <DatasetOverview dataset={dataset} />

      {/* 2. Tab Navigation Switcher Bar */}
      <div className="flex items-center justify-between border-b-2 border-indigo-200/80 pb-3">
        <div className="flex items-center gap-2.5">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4.5 py-2.5 rounded-xl text-xs sm:text-sm font-extrabold flex items-center gap-2 transition ${
                  isActive
                    ? 'bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-700 text-white shadow-md shadow-indigo-600/30 border border-indigo-500'
                    : 'bg-white text-slate-700 hover:text-indigo-900 border border-slate-300 hover:border-indigo-400 shadow-xs'
                }`}
              >
                <Icon className={`h-4.5 w-4.5 ${isActive ? 'text-white' : 'text-indigo-600'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        <div className="hidden sm:flex items-center gap-2 text-xs sm:text-sm font-bold text-slate-700 bg-white border border-indigo-200 px-3 py-1.5 rounded-xl shadow-2xs">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>Session: <code className="font-mono text-xs font-bold text-indigo-700">{dataset.dataset_id?.substring(0, 8)}</code></span>
        </div>
      </div>

      {/* 3. Main Tab Content Area */}
      <div className="flex-1 overflow-hidden min-h-0">
        {/* Tab 1: AI Analyst Chat Split View */}
        {activeTab === 'CHAT' && (
          <div className="h-full grid grid-cols-1 lg:grid-cols-12 gap-4">
            <div className="lg:col-span-8 h-full flex flex-col min-h-0">
              <ChatInterface
                dataset={dataset}
                messages={messages}
                onSendMessage={onSendMessage}
                isWorking={isWorking}
                onClearHistory={onClearHistory}
                onRetry={onRetry}
              />
            </div>
            <div className="lg:col-span-4 h-full overflow-hidden flex flex-col">
              <DatasetInsights dataset={dataset} />
            </div>
          </div>
        )}

        {/* Tab 2: Column Explorer & Schema Grid */}
        {activeTab === 'EXPLORER' && (
          <div className="h-full">
            <ColumnExplorer dataset={dataset} />
          </div>
        )}

        {/* Tab 3: Paginated & Searchable Data Preview Table */}
        {activeTab === 'TABLE' && (
          <div className="h-full">
            <DataPreviewTable
              preview={dataset.preview}
              columnNames={dataset.column_names}
              dtypes={dataset.dtypes}
            />
          </div>
        )}
      </div>
    </div>
  );
}
