import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Trash2, HelpCircle, Loader2 } from 'lucide-react';
import ChatMessage from './ChatMessage';
import AgentActivity from './AgentActivity';

export default function ChatInterface({
  messages,
  onSendMessage,
  isWorking,
  onClearHistory,
  onRetry
}) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const suggestedQuestions = [
    "Which columns have missing values?",
    "What is the average fare?",
    "Compare survival rate by passenger class and create a chart",
    "Fill missing Age values with median",
    "How many missing values are in Age now?"
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isWorking]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || isWorking) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleChipClick = (question) => {
    if (isWorking) return;
    onSendMessage(question);
  };

  const chipThemes = ['card-blue', 'card-emerald', 'card-violet', 'card-amber', 'card-indigo'];

  return (
    <div className="flex flex-col h-full glass-panel rounded-2xl border-2 border-indigo-200/80 overflow-hidden shadow-xl bg-white/80">
      {/* Chat Header */}
      <div className="px-5 py-3.5 border-b-2 border-indigo-200 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-2.5">
          <div className="h-7 w-7 rounded-lg bg-indigo-600/30 border border-indigo-400 flex items-center justify-center">
            <Sparkles className="h-4 w-4 text-indigo-400 animate-pulse" />
          </div>
          <h2 className="text-base font-extrabold text-white tracking-wide">AI Analyst Conversation</h2>
        </div>

        {messages.length > 0 && (
          <button
            onClick={onClearHistory}
            className="text-xs sm:text-sm text-slate-300 hover:text-rose-400 flex items-center gap-1.5 px-3 py-1.5 rounded-xl hover:bg-slate-800 transition font-bold border border-slate-700 hover:border-rose-500"
            title="Clear Chat History"
          >
            <Trash2 className="h-4 w-4" />
            <span>Clear History</span>
          </button>
        )}
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 p-5 overflow-y-auto space-y-5">
        {/* Empty State */}
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-6">
            <div className="h-16 w-16 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-600 p-0.5 shadow-lg shadow-indigo-500/30">
              <div className="h-full w-full bg-white rounded-[14px] flex items-center justify-center text-indigo-600">
                <HelpCircle className="h-8 w-8" />
              </div>
            </div>

            <div className="space-y-2 max-w-md">
              <h3 className="text-xl font-extrabold text-slate-900">Ask anything about your dataset</h3>
              <p className="text-sm text-slate-600 font-medium leading-relaxed">
                Ask analytical questions, request data cleaning, or ask for interactive charts & visualizations.
              </p>
            </div>

            {/* Suggested Question Chips */}
            <div className="w-full max-w-lg space-y-2.5">
              <p className="text-xs font-extrabold text-indigo-800 uppercase tracking-wider text-left">
                Suggested Questions
              </p>
              <div className="flex flex-wrap gap-2 text-left">
                {suggestedQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleChipClick(q)}
                    disabled={isWorking}
                    className={`text-xs sm:text-sm font-bold px-3.5 py-2.5 rounded-xl ${chipThemes[idx % chipThemes.length]} text-slate-800 hover:text-indigo-900 transition text-left shadow-xs flex items-center gap-2 transform hover:-translate-y-0.5`}
                  >
                    <span>💡</span>
                    <span>{q}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Conversation Message List */}
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} onRetry={onRetry} />
        ))}

        {/* Live Agent Working Activity Checklist */}
        {isWorking && <AgentActivity isWorking={true} />}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <form onSubmit={handleSubmit} className="p-4 bg-slate-50 border-t-2 border-indigo-200 flex items-end gap-3">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isWorking ? "Agent is processing your dataset..." : "Ask a question (Enter to send, Shift+Enter for new line)"}
            disabled={isWorking}
            className="w-full bg-white border-2 border-indigo-200 focus:border-indigo-600 rounded-xl px-4 py-3.5 text-sm sm:text-base font-semibold text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition disabled:opacity-50 resize-none max-h-36 min-h-[48px] shadow-sm"
          />
        </div>

        <button
          type="submit"
          disabled={!input.trim() || isWorking}
          className="h-12 px-5 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-700 hover:from-indigo-700 hover:to-purple-700 text-white font-extrabold text-sm sm:text-base flex items-center gap-2 transition disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-indigo-600/30 shrink-0"
        >
          {isWorking ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <>
              <span>Send</span>
              <Send className="h-5 w-5" />
            </>
          )}
        </button>
      </form>
    </div>
  );
}
