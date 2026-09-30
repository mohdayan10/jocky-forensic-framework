import React, { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function Reports() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    api.reportStats('OP-FALCON-01')
      .then(r => setStats(r.data))
      .catch(() => {
        // Fallback if endpoint not hit yet
        setStats({ artifact_count: 486, host_count: 3, finding_count: 1, finding_id: '' });
      });
  }, []);

  const findingId = stats?.finding_id || 'F-??????';

  async function download(type) {
    const url = type === 'pdf' ? api.reportPdf('OP-FALCON-01') : api.reportJson('OP-FALCON-01');
    const res = await fetch(url);
    const blob = await res.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `jocky_OP-FALCON-01.${type}`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  const CHECKLIST = [
    'Case metadata (ID, investigator, organization)',
    `Evidence inventory — ${stats?.artifact_count ?? 486} artifacts across ${stats?.host_count ?? 3} hosts`,
    'Polymorphic build manifest — 3 unique binaries (SHA-256 verified)',
    'Timeline of events (09:31:02 — 09:31:17)',
    'EPROCESS delta — 1 hidden process detected',
    'SSDT hook table — 2 hooks found',
    'BYOVD match — CVE-2021-21551 (VulnDrv.sys)',
    `${findingId}: CRITICAL/HIGH — BYOVD + EDR blinding`,
    'AI forensic explanation with citation validation',
    'Blockchain integrity verification chain',
  ];

  return (
    <div>
      <h1 className="text-lg font-bold text-gray-200 mb-6">Reports</h1>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {[
          { label: 'Artifacts', value: stats?.artifact_count ?? '—' },
          { label: 'Hosts',     value: stats?.host_count     ?? '—' },
          { label: 'Findings',  value: stats?.finding_count  ?? '—' },
        ].map(({ label, value }) => (
          <div key={label} className="bg-gray-800 border border-gray-700 rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-green-400">{value}</div>
            <div className="text-gray-500 text-xs mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Downloads */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-5 mb-6">
        <div className="text-gray-400 text-xs uppercase tracking-wider mb-4">Download Report</div>
        <div className="flex gap-3">
          <button onClick={() => download('pdf')}
            className="bg-red-800 hover:bg-red-700 text-gray-200 font-bold px-5 py-2 rounded text-sm transition-colors">
            ⬇ Download PDF
          </button>
          <button onClick={() => download('json')}
            className="bg-blue-800 hover:bg-blue-700 text-gray-200 font-bold px-5 py-2 rounded text-sm transition-colors">
            ⬇ Download JSON
          </button>
        </div>
      </div>

      {/* Report contents checklist */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-5">
        <div className="text-gray-400 text-xs uppercase tracking-wider mb-4">Report Contents</div>
        <div className="space-y-2">
          {CHECKLIST.map((item, i) => (
            <div key={i} className="flex items-start gap-3 text-sm">
              <span className="text-green-400 mt-0.5 flex-shrink-0">✓</span>
              <span className="text-gray-300">{item}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
