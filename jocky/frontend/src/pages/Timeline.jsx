import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, connectWebSocket } from '../api/client';

const SEV_COLORS = {
  CRITICAL: 'bg-red-900 text-red-400 border-red-700',
  HIGH:     'bg-orange-900 text-orange-400 border-orange-700',
  MEDIUM:   'bg-yellow-900 text-yellow-400 border-yellow-700',
  LOW:      'bg-gray-800 text-gray-400 border-gray-600',
  INFO:     'bg-blue-900 text-blue-400 border-blue-700',
};

export default function Timeline() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newIds, setNewIds] = useState(new Set());
  const bottomRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    api.timeline('OP-FALCON-01', 'HOST-01')
      .then(r => setEvents(r.data.events || []))
      .catch(err => console.error('Timeline fetch failed:', err))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events.length]);

  // Listen for new events via WebSocket
  useEffect(() => {
    const ws = connectWebSocket('OP-FALCON-01', (msg) => {
      if (msg.type === 'EVIDENCE_RECEIVED' && msg.evidence_id) {
        const newEv = {
          timestamp: new Date().toISOString(),
          description: `Evidence received: ${msg.evidence_id} (${msg.artifact_type})`,
          evidence_id: msg.evidence_id,
          severity: 'INFO',
          _live: true,
        };
        setEvents(prev => [...prev, newEv]);
        setNewIds(prev => new Set([...prev, msg.evidence_id]));
      }
    });
    return () => ws.close();
  }, []);

  function fmtTime(ts) {
    return ts?.replace('2026-09-30T', '').replace('Z', '') || ts;
  }

  return (
    <div>
      <h1 className="text-lg font-bold text-gray-200 mb-4">Timeline</h1>

      <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
        <div className="px-4 py-2 border-b border-gray-700 grid grid-cols-12 text-gray-500 text-xs uppercase tracking-wider">
          <span className="col-span-2">Timestamp</span>
          <span className="col-span-6">Event</span>
          <span className="col-span-2">Evidence ID</span>
          <span className="col-span-2">Severity</span>
        </div>
        <div className="max-h-screen overflow-y-auto divide-y divide-gray-750">
          {loading && (
            <div className="px-4 py-3 text-gray-500 text-xs">Loading...</div>
          )}
          {events.map((ev, i) => (
            <div
              key={i}
              className={`grid grid-cols-12 px-4 py-2.5 text-xs items-center transition-all ${
                ev._live ? 'bg-green-950 animate-pulse' : i % 2 === 0 ? 'bg-gray-850' : ''
              }`}
            >
              <span className="col-span-2 text-gray-500 font-mono">{fmtTime(ev.timestamp)}</span>
              <span className="col-span-6 text-gray-300">{ev.description}</span>
              <span className="col-span-2">
                {ev.evidence_id && (
                  <button
                    onClick={() => navigate('/graph')}
                    className="text-green-400 hover:text-green-300 font-mono underline"
                  >
                    {ev.evidence_id}
                  </button>
                )}
              </span>
              <span className="col-span-2">
                {ev.severity && (
                  <span className={`text-xs px-1.5 py-0.5 rounded border ${SEV_COLORS[ev.severity] || SEV_COLORS.INFO}`}>
                    {ev.severity}
                  </span>
                )}
              </span>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  );
}
