import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';

const typeColors = {
  PROCESS:        '#2196f3',
  FILE:           '#4caf50',
  NETWORK:        '#ff9800',
  REGISTRY:       '#e91e63',
  DRIVER:         '#9c27b0',
  HIDDEN_PROCESS: '#f44336',
  USER:           '#607d8b',
};

function EvidenceNode({ data }) {
  const color = typeColors[data.type] || '#666';
  return (
    <div style={{
      padding: '10px 16px',
      borderRadius: 8,
      border: `2px solid ${color}`,
      background: '#111827',
      minWidth: 160,
    }}>
      <Handle type="target" position={Position.Top} />
      <div style={{ color, fontSize: 10, fontWeight: 700, marginBottom: 4 }}>
        {data.type}
      </div>
      <div style={{ color: '#e0e0e0', fontSize: 13, fontWeight: 500 }}>
        {data.label}
      </div>
      {data.id && (
        <div style={{ color: '#888', fontSize: 10, marginTop: 2, fontFamily: 'monospace' }}>
          {data.id}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

export default memo(EvidenceNode);
