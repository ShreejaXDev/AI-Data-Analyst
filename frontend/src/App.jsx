import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import UploadScreen from './components/UploadScreen';
import Workspace from './components/Workspace';
import { uploadDataset, askQuestion, getHealth } from './services/api';

export default function App() {
  const [dataset, setDataset] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isAgentWorking, setIsAgentWorking] = useState(false);
  const [error, setError] = useState(null);
  const [healthStatus, setHealthStatus] = useState('connecting');

  const formatTimestamp = () => {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Check Backend Health on Mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const data = await getHealth();
        if (data && data.status === 'ok') {
          setHealthStatus('ok');
        }
      } catch (err) {
        console.warn('Backend health check failed:', err);
        setHealthStatus('error');
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle CSV Upload (Ensures Dataset State Isolation)
  const handleUpload = async (file) => {
    setIsUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      const data = await uploadDataset(file, (progress) => {
        setUploadProgress(progress);
      });
      // Clear previous dataset state & conversation history to prevent state leaks
      setDataset(data);
      setMessages([]);
    } catch (err) {
      console.error('Upload Error:', err);
      const msg = err.response?.data?.detail || err.message || 'Failed to upload CSV file.';
      setError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  // Handle Asking Question to AI Agent
  const handleSendMessage = async (text) => {
    if (!dataset || !dataset.dataset_id) return;

    const userMessageId = `usr_${Date.now()}`;
    const userMessage = {
      id: userMessageId,
      sender: 'user',
      text: text,
      timestamp: formatTimestamp(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsAgentWorking(true);

    try {
      // Call backend API
      const data = await askQuestion(dataset.dataset_id, text);

      const aiMessage = {
        id: `ai_${Date.now()}`,
        sender: 'ai',
        text: data.answer,
        chart: data.chart,
        actions: data.actions || [],
        timestamp: formatTimestamp(),
        isError: false,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      console.error('Chat Error:', err);
      const errorMessage = {
        id: `err_${Date.now()}`,
        sender: 'ai',
        text: 'Something went wrong while analyzing your dataset.',
        timestamp: formatTimestamp(),
        isError: true,
        originalQuestion: text,
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsAgentWorking(false);
    }
  };

  // Handle Retrying Failed Question
  const handleRetry = (originalQuestion) => {
    if (!originalQuestion || isAgentWorking) return;
    handleSendMessage(originalQuestion);
  };

  // Reset to Upload Screen (Dataset State Isolation)
  const handleNewDataset = () => {
    setDataset(null);
    setMessages([]);
    setError(null);
  };

  // Clear Chat History
  const handleClearHistory = () => {
    setMessages([]);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      <Header
        dataset={dataset}
        onNewDataset={handleNewDataset}
        healthStatus={healthStatus}
      />

      <main className="flex-1 overflow-hidden">
        {!dataset ? (
          <UploadScreen
            onUpload={handleUpload}
            isUploading={isUploading}
            uploadProgress={uploadProgress}
            error={error}
            clearError={() => setError(null)}
          />
        ) : (
          <Workspace
            dataset={dataset}
            messages={messages}
            onSendMessage={handleSendMessage}
            isWorking={isAgentWorking}
            onClearHistory={handleClearHistory}
            onRetry={handleRetry}
          />
        )}
      </main>
    </div>
  );
}
