import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('jocky_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const api = {
  login:         (username, password) => client.post('/auth/login/', { username, password }),
  health:        ()                   => client.get('/health/'),
  getCase:       (caseId)             => client.get(`/auth/cases/${caseId}/`),
  compile:       (source, filename)   => client.post('/compiler/compile/', { source, filename }),
  forgeBuilds:   (caseId)             => client.get(`/forge/builds/${caseId}/`),
  endpoints:     ()                   => client.get('/endpoints/'),
  findings:      (caseId)             => client.get(`/findings/${caseId}/`),
  aiExplain:     (findingId)          => client.get(`/ai/explain/${findingId}/`),
  kernel:        (caseId, host)       => client.get(`/kernel/${caseId}/${host}/`),
  graph:         (caseId, host)       => client.get(`/graph/${caseId}/${host}/`),
  timeline:      (caseId, host)       => client.get(`/timeline/${caseId}/${host}/`),
  blockchainVerify: (evidenceId)      => client.get(`/blockchain/verify/?evidence_id=${evidenceId}`),
  blockchainTamper: (evidenceId)      => client.get(`/blockchain/tamper-demo/?evidence_id=${evidenceId}`),
  reportJson:    (caseId)             => `${API_BASE}/reports/${caseId}/json/`,
  reportPdf:     (caseId)             => `${API_BASE}/reports/${caseId}/pdf/`,
  reportStats:   (caseId)             => client.get(`/reports/${caseId}/`),
  generateReport: (caseId)            => client.get(`/reports/generate/${caseId}/`),
};

export function connectWebSocket(caseId, onMessage) {
  const wsProto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const wsHost = process.env.REACT_APP_WS_URL || 'localhost:8000';
  const ws = new WebSocket(`${wsProto}://${wsHost}/ws/status/${caseId}/`);
  ws.onmessage = (e) => { try { onMessage(JSON.parse(e.data)); } catch {} };
  ws.onerror = (err) => console.warn('WebSocket error:', err);
  return ws;
}

export default client;
