import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2-minute timeout for LLM agent operations
});

export const getHealth = async () => {
  const response = await apiClient.get('/api/health');
  return response.data;
};

export const uploadDataset = async (file, onUploadProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onUploadProgress && progressEvent.total) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onUploadProgress(percentCompleted);
      }
    },
  });

  return response.data;
};

export const askQuestion = async (datasetId, message) => {
  const response = await apiClient.post('/api/chat', {
    dataset_id: datasetId,
    message: message,
  });

  return response.data;
};

export const getFullChartUrl = (chartPath) => {
  if (!chartPath) return null;
  if (chartPath.startsWith('http://') || chartPath.startsWith('https://')) {
    return chartPath;
  }
  const cleanPath = chartPath.startsWith('/') ? chartPath : `/${chartPath}`;
  return `${API_BASE_URL}${cleanPath}`;
};

export default apiClient;
