import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
});

export const getDemoDatasets = () => api.get('/datasets');
export const loadDemoDataset = (id) => api.get(`/datasets/${id}/load`);
export const uploadCSV = (formData) => api.post('/upload', formData);
export const startAudit = (payload) => api.post('/audit', payload);
export const pollStatus = (jobId) => api.get(`/status/${jobId}`);
export const getResults = (jobId) => api.get(`/results/${jobId}`);
export const getExplanations = (jobId) => api.get(`/explain/${jobId}`);
export const applyRemediation = (payload) => api.post('/remediate', payload);
export const downloadReport = (jobId) =>
  api.get(`/report/${jobId}`, { responseType: 'blob' });

export default api;