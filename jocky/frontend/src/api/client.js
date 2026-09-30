import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || '/api';

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
  health:    ()              => client.get('/health/'),
  getCase:   (caseId)        => client.get(`/auth/cases/${caseId}/`),
  compile:   (source, caseId) => client.post('/compiler/compile/', { source, case_id: caseId }),
  deploy:    (targets, caseId) => client.post('/forge/deploy/', { targets, case_id: caseId }),
  findings:  (caseId)        => client.get(`/findings/${caseId}/`),
  verify:    (evidenceId, tamper = false) =>
    client.get(`/blockchain/verify/${evidenceId}/${tamper ? '?tamper=true' : ''}`),
  graph:     (caseId, host)  => client.get(`/graph/${caseId}/${host}/`),
  timeline:  (caseId, host)  => client.get(`/timeline/${caseId}/${host}/`),
  endpoints: ()              => client.get('/endpoints/'),
  query:     (hash, hosts)   => client.get('/query/', { params: { hash, hosts: hosts.join(',') } }),
  explain:   (findingId)     => client.post(`/ai/explain/${findingId}/`),
  generateReport: (caseId)   => client.post(`/reports/generate/${caseId}/`),
};

export function connectWebSocket(caseId, onMessage) {
  const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/status/${caseId}/`;
  const ws = new WebSocket(wsUrl);
  ws.onmessage = (event) => onMessage(JSON.parse(event.data));
  ws.onerror = (err) => console.error('WebSocket error:', err);
  return ws;
}

export default client;
