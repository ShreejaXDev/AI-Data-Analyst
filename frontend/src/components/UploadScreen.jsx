import React, { useState, useRef } from 'react';
import { UploadCloud, AlertCircle, Sparkles, ShieldCheck, Zap, BarChart3 } from 'lucide-react';

export default function UploadScreen({ onUpload, isUploading, uploadProgress, error, clearError }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFile = (file) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.csv')) {
      alert('Only .csv files are supported.');
      return;
    }
    onUpload(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const handleInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  return (
    <div className="min-h-[calc(100vh-75px)] flex flex-col items-center justify-center p-6 relative overflow-hidden bg-slate-100">
      {/* Background Decorative Soft Colorful Gradients */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] bg-gradient-to-tr from-indigo-300/40 via-purple-300/30 to-pink-300/20 blur-[130px] rounded-full pointer-events-none" />

      <div className="w-full max-w-4xl z-10 space-y-9 text-center">
        {/* Hero Tagline */}
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full bg-indigo-100 border border-indigo-300 text-indigo-800 text-xs sm:text-sm font-bold shadow-xs">
            <Sparkles className="h-4 w-4 text-indigo-600 animate-pulse" />
            <span>Autonomous Data Agentic Intelligence</span>
          </div>

          <h1 className="text-5xl sm:text-6xl font-black bg-gradient-to-r from-slate-900 via-indigo-950 to-purple-900 bg-clip-text text-transparent tracking-tight leading-tight">
            AI Data Analyst
          </h1>

          <p className="text-lg sm:text-xl text-slate-700 max-w-2xl mx-auto font-medium leading-relaxed">
            Upload any CSV dataset. Ask natural language questions. Get intelligent reasoning, transformations, and visualizations instantly.
          </p>
        </div>

        {/* Error Alert Card */}
        {error && (
          <div className="p-4.5 rounded-2xl bg-rose-50 border-2 border-rose-300 text-rose-900 flex items-center justify-between text-sm sm:text-base max-w-xl mx-auto shadow-md">
            <div className="flex items-center gap-3 font-bold">
              <AlertCircle className="h-5 w-5 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={clearError} className="text-xs font-bold text-rose-700 hover:text-rose-900 underline">
              Dismiss
            </button>
          </div>
        )}

        {/* Upload Card Dropzone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleBrowseClick}
          className={`relative cursor-pointer p-12 rounded-3xl glass-panel border-3 border-dashed transition-all duration-300 shadow-xl ${
            isDragOver
              ? 'border-indigo-600 bg-indigo-50 scale-[1.01]'
              : 'border-indigo-300 hover:border-indigo-500 bg-white hover:bg-indigo-50/30'
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleInputChange}
            accept=".csv"
            className="hidden"
          />

          <div className="flex flex-col items-center space-y-5">
            <div className="h-20 w-20 rounded-3xl bg-gradient-to-tr from-indigo-500 to-purple-600 p-0.5 shadow-lg shadow-indigo-500/30">
              <div className="h-full w-full bg-white rounded-[22px] flex items-center justify-center text-indigo-600">
                <UploadCloud className="h-10 w-10 animate-bounce" />
              </div>
            </div>

            <div className="space-y-1.5">
              <p className="text-xl sm:text-2xl font-extrabold text-slate-900">
                Drop your CSV dataset here, or <span className="text-indigo-600 underline underline-offset-4 decoration-2">browse files</span>
              </p>
              <p className="text-sm font-medium text-slate-600">
                Supports standard CSV files with any schema, size, or column layout
              </p>
            </div>

            {/* Uploading Progress */}
            {isUploading && (
              <div className="w-full max-w-md mt-4 space-y-2">
                <div className="flex justify-between text-xs sm:text-sm text-slate-800 font-bold">
                  <span>Uploading & Profiling Dataset...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full h-3 bg-slate-200 rounded-full overflow-hidden shadow-inner">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Feature Highlights Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 text-left max-w-3xl mx-auto pt-2">
          <div className="p-5 rounded-2xl card-indigo shadow-sm space-y-2.5 transition hover:shadow-md">
            <div className="p-2 rounded-xl bg-indigo-100 w-fit">
              <Zap className="h-6 w-6 text-indigo-600" />
            </div>
            <h3 className="text-base font-extrabold text-slate-900">Smart Auto-Profiling</h3>
            <p className="text-xs sm:text-sm font-medium text-slate-600">Detects columns, statistics, data types & missing values instantly.</p>
          </div>
          <div className="p-5 rounded-2xl card-violet shadow-sm space-y-2.5 transition hover:shadow-md">
            <div className="p-2 rounded-xl bg-violet-100 w-fit">
              <BarChart3 className="h-6 w-6 text-violet-600" />
            </div>
            <h3 className="text-base font-extrabold text-slate-900">Interactive Charts</h3>
            <p className="text-xs sm:text-sm font-medium text-slate-600">Generates custom Matplotlib visualizations on demand.</p>
          </div>
          <div className="p-5 rounded-2xl card-emerald shadow-sm space-y-2.5 transition hover:shadow-md">
            <div className="p-2 rounded-xl bg-emerald-100 w-fit">
              <ShieldCheck className="h-6 w-6 text-emerald-600" />
            </div>
            <h3 className="text-base font-extrabold text-slate-900">Stateful Transformations</h3>
            <p className="text-xs sm:text-sm font-medium text-slate-600">DataFrame modifications persist across multi-turn questions.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
