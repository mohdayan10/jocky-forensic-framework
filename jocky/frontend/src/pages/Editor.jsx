import React, { useState } from 'react';
import { Typography, Box, Button, Paper, Alert } from '@mui/material';
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

export default function Editor() {
  const [source, setSource] = useState(DEFAULT_SOURCE);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [compiling, setCompiling] = useState(false);

  const handleCompile = async () => {
    setCompiling(true);
    setError(null);
    try {
      const res = await api.compile(source, 'OP-FALCON-01');
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Compilation failed');
    }
    setCompiling(false);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4" sx={{ color: 'primary.main' }}>
          JOCKY Editor
        </Typography>
        <Button variant="contained" onClick={handleCompile} disabled={compiling}>
          {compiling ? 'Compiling...' : 'Compile'}
        </Button>
      </Box>

      <Box sx={{ display: 'flex', gap: 2, height: 'calc(100vh - 200px)' }}>
        <Box sx={{ flex: 1 }}>
          <MonacoEditor
            height="100%"
            language="plaintext"
            theme="vs-dark"
            value={source}
            onChange={(val) => setSource(val || '')}
            options={{ fontSize: 14, minimap: { enabled: false }, wordWrap: 'on' }}
          />
        </Box>

        <Paper sx={{ flex: 1, p: 2, overflow: 'auto' }}>
          <Typography variant="h6" sx={{ mb: 1 }}>JIR Output</Typography>
          {error && <Alert severity="error" sx={{ mb: 1 }}>{String(error)}</Alert>}
          {result && (
            <>
              {result.success ? (
                <Box component="pre" sx={{ fontSize: 12, whiteSpace: 'pre-wrap', color: '#00e676' }}>
                  {result.jir}
                </Box>
              ) : (
                <Alert severity="error">{JSON.stringify(result.error)}</Alert>
              )}
              <Typography variant="caption" color="text.secondary">
                Tokens: {result.token_count} | Statements: {result.statement_count}
              </Typography>
            </>
          )}
        </Paper>
      </Box>
    </Box>
  );
}
