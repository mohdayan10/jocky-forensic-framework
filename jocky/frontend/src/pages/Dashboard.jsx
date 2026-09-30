import React, { useEffect, useState } from 'react';
import { api, connectWebSocket } from '../api/client';

const STATUS_COLORS = {
  PENDING:    'bg-gray-700 text-gray-400',
  COLLECTING: 'bg-yellow-900 text-yellow-400',
  COMPLETE:   'bg-green-900 text-green-400',
};

export default function Dashboard() {
  const [hosts, setHosts] = useState([]);
  const [events, setEvents] = useState([]);
  const [wsStatus, setWsStatus] = useState('connecting');
  const [loading, setLoading] = useState(true);

  function fetchEndpoints() {
    api.endpoints()
      .then(r => {
        const eps = r.data.endpoints || [];
        setHosts(eps.map(ep => ({
          id:       ep.host_id,
          platform: ep.platform,
          status:   ep.status,
          count:    ep.artifact_count,
          buildId:  ep.build_id,
        })));
      })
      .catch(() => {
        setHosts([
          { id: 'HOST-01', platform: 'Windows Server 2019', status: 'PENDING', count: 0, buildId: '—' },
          { id: 'HOST-02', platform: 'Ubuntu 22.04',        status: 'PENDING', count: 0, buildId: '—' },
          { id: 'HOST-03', platform: 'Windows 11',          status: 'PENDING', count: 0, buildId: '—' },
        ]);
      })
      .finally(() => setLoading(false));
  }

  // Initial fetch + poll every 8 seconds
  useEffect(() => {
    fetchEndpoints();
    const t = setInterval(fetchEndpoints, 8000);
    return () => clearInterval(t);
  }, []);

  // WebSocket for live push (requires daphne backend)
  useEffect(() => {
    let ws;
    try {
      ws = connectWebSocket('OP-FALCON-01', (msg) => {
        setEvents(prev => [...prev.slice(-19), { ...msg, ts: new Date().toISOString() }]);
        if (msg.type === 'AGENT_STATUS') {
          setHosts(prev => prev.map(h =>
            h.id === msg.host_id
              ? { ...h, status: msg.status, count: msg.artifact_count ?? h.count }
              : h
          ));
        }
        if (msg.type === 'CONNECTION_ESTABLISHED') setWsStatus('connected');
        if (msg.type === 'FORGE_COMPLETE')     fetchEndpoints();
        if (msg.type === 'FINDING_RAISED')     setEvents(prev => [...prev.slice(-19), { ...msg, ts: new Date().toISOString() }]);
        if (msg.type === 'BLOCKCHAIN_VERIFIED') setEvents(prev => [...prev.slice(-19), { ...msg, ts: new Date().toISOString() }]);
        if (msg.type === 'AI_COMPLETE')        setEvents(prev => [...prev.slice(-19), { ...msg, ts: new Date().toISOString() }]);
      });
      ws.onopen  = () => setWsStatus('connected');
      ws.onclose = () => setWsStatus('polling');   // polling still works via 8s interval
      ws.onerror = () => setWsStatus('polling');
    } catch {
      setWsStatus('polling');
    }
    return () => { try { ws?.close(); } catch {} };
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-lg font-bold text-gray-200">Dashboard</h1>
        <span className={`text-xs px-2 py-1 rounded border ${
          wsStatus === 'connected'
            ? 'border-green-800 text-green-400 bg-green-950'
            : wsStatus === 'polling'
            ? 'border-yellow-800 text-yellow-500 bg-yellow-950'
            : 'border-gray-700 text-gray-500 bg-gray-800'
        }`} title={wsStatus === 'polling' ? 'Polling every 8s — start backend with daphne for live push' : ''}>
          {wsStatus === 'connected' ? '⬤ live' : wsStatus === 'polling' ? '↻ polling' : `WS ${wsStatus}`}
        </span>
      </div>

      {/* Host cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {loading
          ? [1,2,3].map(i => (
              <div key={i} className="bg-gray-800 border border-gray-700 rounded-lg p-4 animate-pulse">
                <div className="h-4 bg-gray-700 rounded w-20 mb-3" />
                <div className="h-3 bg-gray-700 rounded w-32 mb-2" />
                <div className="h-3 bg-gray-700 rounded w-24" />
              </div>
            ))
          : hosts.map(host => (
            <div key={host.id} className="bg-gray-800 border border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-gray-200 font-semibold">{host.id}</span>
                <span className={`text-xs px-2 py-0.5 rounded ${STATUS_COLORS[host.status] || STATUS_COLORS.PENDING}`}>
                  {host.status}
                </span>
              </div>
              <div className="text-gray-500 text-xs mb-2">{host.platform}</div>
              <div className="text-gray-400 text-xs mb-1">
                <span className="text-gray-600">Build: </span>
                <span className="text-yellow-400">{host.buildId}</span>
              </div>
              <div className="text-gray-400 text-xs mb-3">
                <span className="text-gray-600">Artifacts: </span>
                <span className="text-green-400">{host.count}</span>
              </div>
              <div className="h-1 bg-gray-700 rounded overflow-hidden">
                <div className={`h-full rounded transition-all duration-500 ${
                  host.status === 'COMPLETE'   ? 'bg-green-500 w-full' :
                  host.status === 'COLLECTING' ? 'bg-yellow-500 w-2/3 animate-pulse' :
                  'bg-gray-600 w-0'
                }`} />
              </div>
            </div>
          ))}
      </div>

      {/* WebSocket events */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <div className="text-gray-500 text-xs uppercase tracking-wider mb-3">Live Events</div>
        <div className="space-y-1 max-h-48 overflow-y-auto">
          {events.length === 0 && (
            <div className="text-gray-600 text-xs">
              Waiting for events… run <code className="text-green-400">python3 -m jocky.demo</code> in terminal to see live updates
            </div>
          )}
          {events.map((ev, i) => (
            <div key={i} className="text-xs flex gap-3">
              <span className="text-gray-600">{ev.ts?.slice(11, 19)}</span>
              <span className={`${
                ev.type === 'AGENT_STATUS'    ? 'text-yellow-400' :
                ev.type === 'FINDING_RAISED'  ? 'text-red-400' :
                'text-green-400'
              }`}>{ev.type}</span>
              <span className="text-gray-400">
                {ev.host_id || ev.finding_id || ev.message || ''}
                {ev.status ? ` → ${ev.status}` : ''}
                {ev.artifact_count ? ` (${ev.artifact_count})` : ''}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
