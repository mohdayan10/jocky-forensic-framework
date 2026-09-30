import React, { useEffect, useState, useCallback } from 'react';
import { Typography, Box } from '@mui/material';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import 'reactflow/dist/style.css';
import EvidenceNode from '../components/EvidenceNode';
import { api } from '../api/client';

const nodeTypes = { evidence: EvidenceNode };

export default function EvidenceGraph() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);

  useEffect(() => {
    api.graph('OP-FALCON-01', 'HOST-01').then(res => {
      const data = res.data;
      const flowNodes = (data.nodes || []).map((n, i) => ({
        id: n.id,
        type: 'evidence',
        position: { x: (i % 4) * 250 + 50, y: Math.floor(i / 4) * 150 + 50 },
        data: { label: n.label, type: n.type, id: n.id },
      }));
      const flowEdges = (data.edges || []).map((e, i) => ({
        id: `edge-${i}`,
        source: e.source,
        target: e.target,
        label: e.relationship,
        animated: true,
        style: { stroke: '#00e676' },
        labelStyle: { fill: '#aaa', fontSize: 10 },
      }));
      setNodes(flowNodes);
      setEdges(flowEdges);
    }).catch(() => {});
  }, []);

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 2, color: 'primary.main' }}>
        Evidence Graph
      </Typography>
      <Box sx={{ height: 'calc(100vh - 200px)', border: '1px solid #1e293b', borderRadius: 1 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background color="#1e293b" gap={20} />
          <Controls />
          <MiniMap nodeStrokeColor="#00e676" />
        </ReactFlow>
      </Box>
    </Box>
  );
}
