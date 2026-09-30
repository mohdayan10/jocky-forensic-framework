import React, { useEffect, useState, useCallback } from 'react';
import ReactFlow, { Controls, Background, useNodesState, useEdgesState } from 'reactflow';
import 'reactflow/dist/style.css';
import { api } from '../api/client';

const TYPE_COLORS = {
  process:  '#3b82f6',
  network:  '#f97316',
  file:     '#22c55e',
  registry: '#a855f7',
  driver:   '#ef4444',
  kernel:   '#7f1d1d',
  hidden:   '#dc2626',
  user:     '#64748b',
};

const EVIDENCE_DETAIL = {
  'E-00421': { type: 'process', pid: 4821, ppid: 6748, name: 'cmd.exe', path: 'C:\\Windows\\System32\\cmd.exe', cmdline: 'cmd.exe /c powershell.exe -nop -w hidden -enc...', sha256: 'aab4d16a4e8fcab9b59e1a61a5c7a5c7f12ab3c', signature: 'SIGNED', user: 'jdoe', start_time: '09:31:04', host: 'HOST-01' },
  'E-00455': { type: 'process', pid: 4892, ppid: 4821, name: 'powershell.exe', path: 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe', cmdline: 'powershell.exe -nop -w hidden -enc JABzAD0...', sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1c', signature: 'SIGNED', user: 'jdoe', start_time: '09:31:05', host: 'HOST-01' },
  'E-00422': { type: 'file', path: 'C:\\Users\\jdoe\\AppData\\Local\\Temp\\svc.exe', sha256: 'f4a2b8c3d1e9f7a6b2c4d8e1f3a7b9c2d4e6f8a1', signature: 'UNSIGNED', modified: '09:31:10', host: 'HOST-01' },
  'E-00431': { type: 'network', local: '10.0.1.45:49821', remote: '185.220.101.42:443', protocol: 'TCP', state: 'ESTABLISHED', owning_process: 'powershell.exe', pid: 4892, host: 'HOST-01' },
  'E-00438': { type: 'registry', key: 'HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run', value_name: 'WindowsUpdater', value_data: 'C:\\Users\\jdoe\\AppData\\Local\\Temp\\svc.exe', written_at: '09:31:13', host: 'HOST-01' },
  'E-00441': { type: 'driver', name: 'VulnDrv.sys', sha256: 'd4e1f2a3b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0', load_time: '09:31:08', loaded_by: 'powershell.exe', cve: 'CVE-2021-21551', exploit_type: 'Arbitrary kernel read/write via IOCTL', blocklist: 'YES', host: 'HOST-01' },
  'E-00447': { type: 'kernel', event: 'Kernel callback removed', detail: 'PsSetCreateProcessNotifyRoutine entry removed', time: '09:31:09', host: 'HOST-01' },
  'E-00460': { type: 'hidden', name: 'svc_hidden.exe', pid: 4821, eprocess: '0xFFFF8A01C3B40080', path: 'C:\\Users\\jdoe\\AppData\\Local\\Temp\\svc_hidden.exe', detected_by: 'EPROCESS walk delta (94 vs 93)', host: 'HOST-01' },
};

const CRITICAL_NODES = new Set(['E-00441', 'E-00460']);

function buildNodes(apiNodes) {
  const cols = { process: 0, network: 2, file: 1, registry: 1, driver: 0, kernel: 0, hidden: 2, user: 0 };
  const rows = {};
  return apiNodes.map((n) => {
    const type = (n.type || 'process').toLowerCase();
    const col = cols[type] ?? 1;
    rows[col] = (rows[col] || 0) + 1;
    const row = rows[col];
    const color = TYPE_COLORS[type] || '#94a3b8';
    const isCritical = CRITICAL_NODES.has(n.id);
    return {
      id: n.id,
      position: { x: col * 300 + 50, y: row * 110 },
      data: { label: (
        <div style={{ fontSize: 11, fontFamily: 'monospace' }}>
          <div style={{ fontWeight: 700, color: isCritical ? '#ef4444' : color }}>{n.id}</div>
          <div style={{ color: '#94a3b8', marginTop: 2 }}>{n.label}</div>
          {isCritical && <div style={{ color: '#ef4444', fontSize: 9, marginTop: 2 }}>◉ CRITICAL</div>}
        </div>
      ), raw: n },
      style: {
        background: isCritical ? '#1a0a0a' : '#1e293b',
        border: `1px solid ${isCritical ? '#ef4444' : color}`,
        borderRadius: 6,
        padding: '6px 10px',
        minWidth: 160,
      },
    };
  });
}

function buildEdges(apiEdges) {
  return apiEdges.map((e, i) => ({
    id: `edge-${i}`,
    source: e.source,
    target: e.target,
    label: e.relationship,
    style: { stroke: '#4b5563' },
    labelStyle: { fill: '#9ca3af', fontSize: 10, fontFamily: 'monospace' },
  }));
}

function Row({ label, value, red }) {
  if (!value && value !== 0) return null;
  return (
    <div className="flex gap-2 mb-1.5 text-xs">
      <span className="text-gray-600 flex-shrink-0 w-28">{label}</span>
      <span className={`font-mono break-all ${red ? 'text-red-400' : 'text-green-400'}`}>{String(value)}</span>
    </div>
  );
}

function DetailPanel({ nodeId, onClose }) {
  const ev = EVIDENCE_DETAIL[nodeId];
  const isCritical = CRITICAL_NODES.has(nodeId);

  return (
    <div className="w-72 bg-gray-800 border border-gray-700 rounded-lg flex flex-col overflow-hidden flex-shrink-0">
      <div className={`px-4 py-3 border-b border-gray-700 flex items-start justify-between ${isCritical ? 'bg-red-950' : ''}`}>
        <div>
          <div className="text-green-400 font-mono text-sm font-bold">{nodeId}</div>
          <div className="text-gray-500 text-xs mt-0.5 capitalize">{ev?.type || 'unknown'} artifact · {ev?.host}</div>
          {isCritical && (
            <span className="inline-block mt-1 text-xs px-2 py-0.5 rounded bg-red-900 border border-red-700 text-red-300 font-bold">
              ◉ CRITICAL
            </span>
          )}
        </div>
        <button onClick={onClose} className="text-gray-600 hover:text-gray-300 text-xl leading-none ml-2">×</button>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {!ev ? (
          <div className="text-gray-600 text-xs">No detail available for this node.</div>
        ) : ev.type === 'process' ? (<>
          <Row label="Name"      value={ev.name} />
          <Row label="PID"       value={ev.pid} />
          <Row label="PPID"      value={ev.ppid} />
          <Row label="User"      value={ev.user} />
          <Row label="Start"     value={ev.start_time} />
          <Row label="Signature" value={ev.signature} red={ev.signature === 'UNSIGNED'} />
          <Row label="Path"      value={ev.path} />
          <Row label="Cmdline"   value={ev.cmdline} />
          <Row label="SHA-256"   value={ev.sha256} />
        </>) : ev.type === 'network' ? (<>
          <Row label="Process"  value={ev.owning_process} />
          <Row label="PID"      value={ev.pid} />
          <Row label="Local"    value={ev.local} />
          <Row label="Remote"   value={ev.remote} />
          <Row label="Protocol" value={ev.protocol} />
          <Row label="State"    value={ev.state} />
        </>) : ev.type === 'file' ? (<>
          <Row label="Path"      value={ev.path} />
          <Row label="SHA-256"   value={ev.sha256} />
          <Row label="Signature" value={ev.signature} red={ev.signature === 'UNSIGNED'} />
          <Row label="Modified"  value={ev.modified} />
          <Row label="Host"      value={ev.host} />
        </>) : ev.type === 'driver' ? (<>
          <Row label="Name"       value={ev.name} />
          <Row label="CVE"        value={ev.cve} red />
          <Row label="Capability" value={ev.exploit_type} />
          <Row label="Blocklist"  value={ev.blocklist} red />
          <Row label="Loaded by"  value={ev.loaded_by} />
          <Row label="Load time"  value={ev.load_time} />
          <Row label="SHA-256"    value={ev.sha256} />
        </>) : ev.type === 'registry' ? (<>
          <Row label="Key"        value={ev.key} />
          <Row label="Value name" value={ev.value_name} />
          <Row label="Value data" value={ev.value_data} />
          <Row label="Written at" value={ev.written_at} />
          <Row label="Host"       value={ev.host} />
        </>) : ev.type === 'kernel' ? (<>
          <Row label="Event"  value={ev.event} />
          <Row label="Detail" value={ev.detail} red />
          <Row label="Time"   value={ev.time} />
          <Row label="Host"   value={ev.host} />
        </>) : ev.type === 'hidden' ? (<>
          <Row label="Name"        value={ev.name} />
          <Row label="PID"         value={ev.pid} red />
          <Row label="EPROCESS"    value={ev.eprocess} />
          <Row label="Path"        value={ev.path} />
          <Row label="Detected by" value={ev.detected_by} />
          <Row label="Host"        value={ev.host} />
        </>) : (
          Object.entries(ev).filter(([k]) => k !== 'type').map(([k, v]) => (
            <Row key={k} label={k} value={v} />
          ))
        )}
      </div>
    </div>
  );
}

export default function EvidenceGraph() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.graph('OP-FALCON-01', 'HOST-01')
      .then(r => {
        setNodes(buildNodes(r.data.nodes || []));
        setEdges(buildEdges(r.data.edges || []));
      })
      .catch(err => console.error('Graph fetch failed:', err))
      .finally(() => setLoading(false));
  }, []);

  const onNodeClick = useCallback((_, node) => setSelected(node.id), []);

  return (
    <div>
      <h1 className="text-lg font-bold text-gray-200 mb-4">Evidence Graph</h1>

      <div className="flex gap-3 mb-4 flex-wrap">
        {Object.entries(TYPE_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1.5 text-xs text-gray-400">
            <span className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: color }} />
            {type}
          </div>
        ))}
      </div>

      <div className="flex gap-4" style={{ height: 'calc(100vh - 220px)' }}>
        <div className="flex-1 bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-full text-gray-500 text-sm">Loading graph...</div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
              fitView
              style={{ background: '#0f172a' }}
            >
              <Background color="#1e293b" gap={24} />
              <Controls style={{ background: '#1e293b', border: '1px solid #374151' }} />
            </ReactFlow>
          )}
        </div>

        {selected ? (
          <DetailPanel nodeId={selected} onClose={() => setSelected(null)} />
        ) : (
          <div className="w-72 bg-gray-800 border border-gray-700 rounded-lg flex items-center justify-center flex-shrink-0">
            <div className="text-gray-600 text-xs text-center px-4">
              Click any node<br />to see full evidence detail
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
