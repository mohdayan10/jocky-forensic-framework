import React, { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function KernelState() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.kernel('OP-FALCON-01', 'HOST-01')
      .then(r => setData(r.data))
      .catch(err => console.error('Kernel fetch failed:', err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-gray-500 text-sm">Loading kernel state...</div>;
  if (!data) return null;

  const { eprocess, ssdt_hooks, byovd_matches } = data;

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-bold text-gray-200">Kernel State</h1>

      {/* EPROCESS Delta */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
        <div className="px-4 py-2 border-b border-gray-700 text-gray-400 text-xs uppercase tracking-wider">
          EPROCESS Delta Table — ActiveProcessLinks Walk vs NtQuerySystemInformation
        </div>
        <div className="p-4">
          <div className="flex gap-8 mb-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-200">{eprocess.walk_count}</div>
              <div className="text-gray-600 text-xs">EPROCESS Walk</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-200">{eprocess.api_count}</div>
              <div className="text-gray-600 text-xs">API Result</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-400">{eprocess.delta}</div>
              <div className="text-gray-600 text-xs">Delta (Hidden)</div>
            </div>
          </div>
          {eprocess.hidden?.length > 0 && (
            <div className="bg-red-950 border border-red-800 rounded p-3">
              <div className="text-red-400 text-xs uppercase tracking-wider mb-2">Hidden Processes Detected</div>
              {eprocess.hidden.map((p, i) => (
                <div key={i} className="text-xs grid grid-cols-3 gap-3">
                  <span className="text-red-300 font-bold">{p.name}</span>
                  <span className="text-red-400">PID {p.pid}</span>
                  <span className="text-gray-400 font-mono truncate">{p.path}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* SSDT Hooks */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
        <div className="px-4 py-2 border-b border-gray-700 text-gray-400 text-xs uppercase tracking-wider">
          SSDT Hook Table
        </div>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-700 text-gray-500 uppercase">
              <th className="text-left px-4 py-2">Syscall</th>
              <th className="text-left px-4 py-2">Expected Module</th>
              <th className="text-left px-4 py-2">Found Module</th>
              <th className="text-left px-4 py-2">Hook Type</th>
            </tr>
          </thead>
          <tbody>
            {ssdt_hooks?.map((h, i) => (
              <tr key={i} className="border-b border-gray-750 bg-orange-950">
                <td className="px-4 py-2.5 text-orange-300 font-mono">{h.syscall}</td>
                <td className="px-4 py-2.5 text-gray-400">{h.expected}</td>
                <td className="px-4 py-2.5 text-red-400">{h.found}</td>
                <td className="px-4 py-2.5">
                  <span className="px-2 py-0.5 rounded bg-red-900 text-red-400 border border-red-700">
                    {h.hook_type}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* BYOVD Matches */}
      {byovd_matches?.map((m, i) => (
        <div key={i} className="bg-gray-800 border border-red-800 rounded-lg overflow-hidden">
          <div className="px-4 py-2 border-b border-red-800 text-red-400 text-xs uppercase tracking-wider flex items-center gap-2">
            <span>⚠</span> BYOVD Match
          </div>
          <div className="p-4 space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-gray-600 text-xs">Driver: </span>
                <span className="text-red-300 font-mono">{m.driver}</span>
              </div>
              <div>
                <span className="text-gray-600 text-xs">CVE: </span>
                <span className="text-red-400">{m.cve}</span>
              </div>
              <div className="col-span-2">
                <span className="text-gray-600 text-xs">Capability: </span>
                <span className="text-gray-300">{m.capability}</span>
              </div>
              <div>
                <span className="text-gray-600 text-xs">Microsoft Blocklist: </span>
                <span className={m.blocklisted ? 'text-red-400' : 'text-gray-400'}>
                  {m.blocklisted ? 'YES ✗' : 'NO'}
                </span>
              </div>
            </div>

            {m.attack_chain?.length > 0 && (
              <div>
                <div className="text-gray-600 text-xs uppercase tracking-wider mb-2">Attack Chain</div>
                <div className="space-y-1">
                  {m.attack_chain.map((step, j) => (
                    <div key={j} className="flex gap-3 text-xs">
                      <span className="text-yellow-400 font-mono w-20 flex-shrink-0">{step.time}</span>
                      <span className="text-gray-300">{step.event}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
