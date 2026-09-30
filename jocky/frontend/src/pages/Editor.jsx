import React, { useState } from 'react';
import MonacoEditor from '@monaco-editor/react';
import { api } from '../api/client';

const DEFAULT_SOURCE = `case "OP-FALCON-01"
target hostgroup ENTERPRISE_EAST

collect processes
collect network
collect persistence
collect drivers
collect file_metadata WHERE path IN ["Temp", "AppData"]
                       AND modified_within "72h"
collect kernel_callbacks
collect hook_state
collect hidden_processes

correlate processes WITH network WITHIN 45 seconds
correlate processes WITH files
correlate users WITH processes

detect unsigned_executable_in_temp
detect byovd_loaded_driver
detect suspicious_process_chain
detect lateral_movement
detect persistence_anomaly

timeline
evidence_graph
generate report FORMAT [json, pdf]
`;

function beforeMount(monaco) {
  monaco.languages.register({ id: 'jocky' });
  monaco.languages.setMonarchTokensProvider('jocky', {
    keywords: ['case', 'target', 'collect', 'correlate', 'detect', 'timeline', 'evidence_graph', 'generate', 'report'],
    operators: ['WHERE', 'AND', 'OR', 'WITH', 'WITHIN', 'FORMAT', 'IN'],
    tokenizer: {
      root: [
        [/\b(case|target|collect|correlate|detect|timeline|evidence_graph|generate|report)\b/, 'keyword'],
        [/\b(WHERE|AND|OR|WITH|WITHIN|FORMAT|IN)\b/, 'type'],
        [/"[^"]*"/, 'string'],
        [/#.*$/, 'comment'],
        [/\d+[smh]/, 'number'],
        [/\[|\]/, 'delimiter'],
      ],
    },
  });
  monaco.editor.defineTheme('jocky-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'keyword', foreground: '4ade80', fontStyle: 'bold' },
      { token: 'type',    foreground: 'fbbf24' },
      { token: 'string',  foreground: 'a78bfa' },
      { token: 'comment', foreground: '6b7280', fontStyle: 'italic' },
      { token: 'number',  foreground: 'fb923c' },
    ],
    colors: {
      'editor.background': '#0f1929',
      'editor.foreground': '#e2e8f0',
      'editor.lineHighlightBackground': '#1e293b',
      'editorLineNumber.foreground': '#374151',
    },
  });
}

export default function Editor() {
  const [source, setSource] = useState(DEFAULT_SOURCE);
  const [output, setOutput] = useState('');
  const [status, setStatus] = useState(null); // 'PASSED' | 'REJECTED' | null
  const [loading, setLoading] = useState(false);

  async function compile() {
    setLoading(true);
    setOutput('');
    setStatus(null);
    try {
      const res = await api.compile(source, 'op_falcon.jky');
      const d = res.data;
      if (d.success) {
        setStatus('PASSED');
        setOutput(d.jir || '');
      } else {
        setStatus('REJECTED');
        setOutput(Array.isArray(d.error) ? d.error.join('\n') : (d.error || 'Compilation failed'));
      }
    } catch (err) {
      setStatus('REJECTED');
      setOutput(err.response?.data?.error || 'Server error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-bold text-gray-200">Editor</h1>
        <div className="flex items-center gap-3">
          {status && (
            <span className={`text-xs px-3 py-1 rounded border font-bold ${
              status === 'PASSED'
                ? 'bg-green-950 border-green-700 text-green-400'
                : 'bg-red-950 border-red-700 text-red-400'
            }`}>
              [POLICY] {status}
            </span>
          )}
          <button
            onClick={compile}
            disabled={loading}
            className="bg-green-600 hover:bg-green-500 disabled:bg-gray-700 text-gray-900 font-bold px-4 py-1.5 rounded text-sm transition-colors"
          >
            {loading ? 'Compiling...' : '▶ Compile'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4" style={{ height: 'calc(100vh - 160px)' }}>
        {/* Editor */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
          <div className="text-gray-500 text-xs px-3 py-1.5 border-b border-gray-700 bg-gray-850">
            op_falcon.jky
          </div>
          <MonacoEditor
            height="calc(100% - 32px)"
            language="jocky"
            theme="jocky-dark"
            value={source}
            onChange={v => setSource(v || '')}
            beforeMount={beforeMount}
            options={{
              fontSize: 13,
              fontFamily: '"JetBrains Mono", monospace',
              minimap: { enabled: false },
              lineNumbers: 'on',
              scrollBeyondLastLine: false,
              wordWrap: 'on',
            }}
          />
        </div>

        {/* Output */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden flex flex-col">
          <div className="text-gray-500 text-xs px-3 py-1.5 border-b border-gray-700 flex items-center gap-2">
            JIR Output
            {status && (
              <span className={`text-xs ${status === 'PASSED' ? 'text-green-400' : 'text-red-400'}`}>
                — {status === 'PASSED' ? 'POLICY PASSED ✓' : 'POLICY REJECTED ✗'}
              </span>
            )}
          </div>
          <pre className="flex-1 overflow-auto p-3 text-xs text-gray-300 whitespace-pre-wrap">
            {output || <span className="text-gray-600">Click Compile to see JIR output...</span>}
          </pre>
        </div>
      </div>
    </div>
  );
}
