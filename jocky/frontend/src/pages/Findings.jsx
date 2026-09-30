import React, { useEffect, useState } from 'react';
import { api, connectWebSocket } from '../api/client';

export default function Findings() {
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [explaining, setExplaining] = useState(null);
  const [explanations, setExplanations] = useState({});

  function fetchFindings() {
    api.findings('OP-FALCON-01')
      .then(r => setFindings(r.data.findings || []))
      .catch(err => console.error('Findings fetch failed:', err))
      .finally(() => setLoading(false));
  }

  // Initial fetch + poll every 8 s
  useEffect(() => {
    fetchFindings();
    const t = setInterval(fetchFindings, 8000);
    return () => clearInterval(t);
  }, []);

  // Re-fetch immediately on FINDING_RAISED WebSocket event
  useEffect(() => {
    const ws = connectWebSocket('OP-FALCON-01', (msg) => {
      if (msg.type === 'FINDING_RAISED') fetchFindings();
    });
    return () => ws.close();
  }, []);

  async function explain(finding) {
    setExplaining(finding.finding_id);
    try {
      const res = await api.aiExplain(finding.finding_id);
      setExplanations(prev => ({ ...prev, [finding.finding_id]: res.data }));
    } catch (err) {
      setExplanations(prev => ({
        ...prev,
        [finding.finding_id]: { explanation: 'API error: ' + (err.message || 'unknown'), status: 'ERROR' },
      }));
    } finally {
      setExplaining(null);
    }
  }

  const SEV = {
    CRITICAL: 'bg-red-900 text-red-400 border-red-700',
    HIGH:     'bg-orange-900 text-orange-400 border-orange-700',
    MEDIUM:   'bg-yellow-900 text-yellow-400 border-yellow-700',
    LOW:      'bg-gray-800 text-gray-400 border-gray-600',
  };

  return (
    <div>
      <h1 className="text-lg font-bold text-gray-200 mb-6">Findings</h1>

      {loading && <div className="text-gray-500 text-sm">Loading...</div>}

      {findings.map(f => {
        const exp = explanations[f.finding_id];
        return (
          <div key={f.finding_id} className="bg-gray-800 border border-gray-700 rounded-lg p-5 mb-4">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="text-gray-200 font-bold text-base">{f.finding_id}</span>
                <span className={`text-xs px-2 py-0.5 rounded border font-bold ${SEV[f.severity] || SEV.LOW}`}>
                  {f.severity}
                </span>
                <span className="text-xs px-2 py-0.5 rounded border border-blue-700 bg-blue-950 text-blue-400">
                  {f.confidence}
                </span>
              </div>
              <button
                onClick={() => explain(f)}
                disabled={explaining === f.finding_id}
                className="bg-green-700 hover:bg-green-600 disabled:bg-gray-700 text-gray-900 font-bold px-4 py-1.5 rounded text-sm transition-colors"
              >
                {explaining === f.finding_id ? '⏳ Querying AI...' : '🤖 Ask AI'}
              </button>
            </div>

            <div className="text-gray-400 text-sm mb-4">{f.description}</div>

            {/* Rules fired */}
            <div className="mb-3">
              <div className="text-gray-600 text-xs uppercase tracking-wider mb-2">Rules Fired ({f.rules_fired?.length})</div>
              <div className="flex flex-wrap gap-1.5">
                {(f.rules_fired || []).map(r => (
                  <span key={r} className="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-300 font-mono">
                    {r}
                  </span>
                ))}
              </div>
            </div>

            {/* Evidence IDs */}
            <div className="mb-4">
              <div className="text-gray-600 text-xs uppercase tracking-wider mb-2">Evidence ({f.evidence_ids?.length})</div>
              <div className="flex flex-wrap gap-1.5">
                {(f.evidence_ids || []).map(eid => (
                  <span key={eid} className="text-xs px-2 py-0.5 rounded bg-green-950 text-green-400 font-mono border border-green-800">
                    {eid}
                  </span>
                ))}
              </div>
            </div>

            {/* AI Explanation */}
            {exp && (
              <div className="mt-4 border-t border-gray-700 pt-4">
                <div className="text-gray-500 text-xs uppercase tracking-wider mb-2">AI Explanation</div>
                <div className="bg-gray-900 border border-gray-700 rounded p-4 text-sm text-gray-300 whitespace-pre-wrap mb-3">
                  {exp.explanation || 'No explanation returned.'}
                </div>
                {/* Citation validation */}
                <div className={`text-xs px-3 py-2 rounded border ${
                  exp.status === 'VALIDATED'
                    ? 'bg-green-950 border-green-700 text-green-400'
                    : exp.status === 'REJECTED'
                    ? 'bg-red-950 border-red-700 text-red-400'
                    : 'bg-gray-800 border-gray-600 text-gray-400'
                }`}>
                  {exp.status === 'VALIDATED' && '✓ VALIDATED — all citations verified against case record'}
                  {exp.status === 'REJECTED'  && '✗ REJECTED — invalid citation detected'}
                  {exp.status === 'ERROR'     && '⚠ API Error'}
                </div>
                {exp.cited_ids?.length > 0 && (
                  <div className="text-xs text-gray-500 mt-2">
                    Cited: {exp.cited_ids.join(', ')} ·
                    Valid: {exp.valid_ids?.join(', ')} ·
                    Invalid: {exp.invalid_ids?.join(', ') || 'none'}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
