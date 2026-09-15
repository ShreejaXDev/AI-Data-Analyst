import React, { useState } from 'react';
import { Bot, CheckCircle2, Loader2, ChevronDown, ChevronUp } from 'lucide-react';

const ACTION_LABELS = {
  ANALYZE: 'Analyzing your data',
  TRANSFORM: 'Updating the dataset',
  VISUALIZE: 'Creating visualization',
  REPLAN: 'Reconsidering the analysis',
  EXPORT_DATA: 'Preparing dataset export',
  FINISH: 'Finalizing answer',
};

export default function AgentActivity({ isWorking, actions = [] }) {
  const [isOpen, setIsOpen] = useState(true);

  // If actions are provided from backend, render them; otherwise render default workflow steps
  const renderSteps = () => {
    if (actions && actions.length > 0) {
      return actions.map((act, idx) => {
        const actionType = act.action ? act.action.toUpperCase() : 'ANALYZE';
        const label = ACTION_LABELS[actionType] || actionType;
        const desc = act.description ? `: ${act.description}` : '';
        const isLast = idx === actions.length - 1;
        const isDone = !isWorking || !isLast || actionType === 'FINISH';

        return (
          <div key={idx} className="flex items-start gap-2.5 text-slate-800 text-xs sm:text-sm font-semibold">
            {isDone ? (
              <CheckCircle2 className="h-4.5 w-4.5 text-emerald-600 shrink-0 mt-0.5" />
            ) : (
              <Loader2 className="h-4.5 w-4.5 text-indigo-600 animate-spin shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              <span className={`font-bold ${isDone ? 'text-slate-900' : 'text-indigo-700 font-extrabold'}`}>
                {label}
              </span>
              {desc && <span className="text-slate-600 font-normal"> {desc}</span>}
            </div>
          </div>
        );
      });
    }

    // Default fallback loading state while waiting for initial backend response
    const defaultSteps = [
      { label: 'Inspecting dataset profile & column schemas', done: true },
      { label: 'Formulating step-by-step analysis plan', done: true },
      { label: 'Executing Python Pandas analysis & reasoning', done: !isWorking },
      { label: 'Generating visualization & final analyst report', done: !isWorking },
    ];

    return defaultSteps.map((step, idx) => (
      <div key={idx} className="flex items-center gap-2.5 text-slate-800 text-xs sm:text-sm font-semibold">
        {step.done ? (
          <CheckCircle2 className="h-4.5 w-4.5 text-emerald-600 shrink-0" />
        ) : isWorking && idx === 2 ? (
          <Loader2 className="h-4.5 w-4.5 text-indigo-600 animate-spin shrink-0" />
        ) : (
          <div className="h-4 w-4 rounded-full border-2 border-slate-300 shrink-0 bg-slate-100" />
        )}
        <span className={step.done ? 'text-slate-900 font-bold' : 'text-slate-500 font-medium'}>
          {step.label}
        </span>
      </div>
    ));
  };

  return (
    <div className="w-full my-3.5 rounded-2xl bg-indigo-50/80 border-2 border-indigo-200 overflow-hidden shadow-sm">
      {/* Accordion Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 flex items-center justify-between bg-gradient-to-r from-indigo-100 to-purple-100 hover:from-indigo-200 hover:to-purple-200 transition text-left border-b border-indigo-200/80"
      >
        <div className="flex items-center gap-2.5">
          <div className="h-7 w-7 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-xs">
            <Bot className="h-4 w-4" />
          </div>
          <span className="text-xs sm:text-sm font-extrabold text-indigo-950">
            {isWorking ? 'Agent Working & Reasoning...' : 'Agent Execution History'}
          </span>
          {isWorking && (
            <span className="relative flex h-2.5 w-2.5 ml-1">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-indigo-600"></span>
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-indigo-800 font-mono font-extrabold px-2 py-0.5 rounded bg-white border border-indigo-200">
            {isWorking ? 'Processing' : 'Completed'}
          </span>
          {isOpen ? (
            <ChevronUp className="h-4 w-4 text-indigo-700" />
          ) : (
            <ChevronDown className="h-4 w-4 text-indigo-700" />
          )}
        </div>
      </button>

      {/* Accordion Body */}
      {isOpen && (
        <div className="p-4 space-y-2.5 border-t border-indigo-100 text-xs sm:text-sm bg-white/90">
          {renderSteps()}
        </div>
      )}
    </div>
  );
}
