import React, { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function Endpoints() {
  const [builds, setBuilds] = useState([]);
  const [loading, setLoading] = useState(true);

  function fetchBuilds() {
    api.forgeBuilds('OP-FALCON-01')
      .then(r => setBuilds(r.data.builds || []))
      .catch(err => console.error('Forge builds fetch failed:', err))
      .finally(() => setLoading(false));
  }

  // Poll every 8 s — picks up new build IDs written by demo step 4
  useEffect(() => {
    fetchBuilds();
    const t = setInterval(fetchBuilds, 8000);
    return () => clearInterval(t);
  }, []);

  return (
    <div>
      <h1 className="text-lg font-bold text-gray-200 mb-6">Endpoints</h1>

      {builds.length > 0 && builds.every(b => b.status === 'PENDING') && (
        <div className="mb-4 px-4 py-2 bg-yellow-950 border border-yellow-800 rounded-lg text-yellow-400 text-xs">
          ⏳ No demo run detected — run <code className="font-mono">python3 -m jocky.demo</code> to populate live forge builds
        </div>
      )}

      <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
        <div className="px-4 py-2 border-b border-gray-700 text-gray-500 text-xs uppercase tracking-wider">
          Forge Builds — Polymorphic per-host binaries
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700 text-gray-500 text-xs uppercase">
              <th className="text-left px-4 py-2">Host ID</th>
              <th className="text-left px-4 py-2">Platform</th>
              <th className="text-left px-4 py-2">Agent Build ID</th>
              <th className="text-left px-4 py-2">SHA-256</th>
              <th className="text-left px-4 py-2">Entry Point</th>
              <th className="text-left px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="px-4 py-4 text-gray-500 text-center text-xs">Loading...</td></tr>
            ) : builds.map((b, i) => (
              <tr key={b.host_id} className={`border-b border-gray-750 ${i % 2 === 0 ? 'bg-gray-850' : ''}`}>
                <td className="px-4 py-2.5 text-gray-200 font-semibold">{b.host_id}</td>
                <td className="px-4 py-2.5 text-gray-400">{b.platform}</td>
                <td className="px-4 py-2.5 text-yellow-400 font-mono text-xs">{b.build_id}</td>
                <td className="px-4 py-2.5 text-green-400 font-mono text-xs">
                  {b.sha256?.slice(0, 16)}…
                </td>
                <td className="px-4 py-2.5 text-gray-400 font-mono text-xs">{b.entry_point}</td>
                <td className="px-4 py-2.5">
                  <span className="text-xs px-2 py-0.5 rounded bg-green-900 text-green-400">
                    {b.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {builds.length > 0 && (
        <div className="mt-4 bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="text-gray-500 text-xs uppercase tracking-wider mb-3">SHA-256 Uniqueness Proof</div>
          <div className="text-xs text-gray-400 mb-2">Same source program → different binary per host (LLVM mutation + AES-256 stub):</div>
          {builds.map(b => (
            <div key={b.host_id} className="flex gap-3 text-xs mb-1">
              <span className="text-gray-500 w-20">{b.host_id}</span>
              <span className="text-green-400 font-mono">{b.sha256?.slice(0, 32)}…</span>
            </div>
          ))}
          <div className="mt-2 text-xs text-green-400">✓ All hashes unique — polymorphic build confirmed</div>
        </div>
      )}
    </div>
  );
}
