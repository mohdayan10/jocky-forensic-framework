import React, { useEffect, useState } from 'react';
import { Typography, Box, Paper, Chip, Divider } from '@mui/material';
import { api } from '../api/client';

export default function CaseManager() {
  const [caseData, setCaseData] = useState(null);

  useEffect(() => {
    api.getCase('OP-FALCON-01').then(res => setCaseData(res.data)).catch(() => {});
  }, []);

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, color: 'primary.main' }}>Case Manager</Typography>

      {caseData ? (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h5" sx={{ fontFamily: 'monospace' }}>{caseData.case_id}</Typography>
            <Chip label="ACTIVE" color="success" />
          </Box>
          <Divider sx={{ mb: 2 }} />
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <Box>
              <Typography variant="caption" color="text.secondary">Investigator</Typography>
              <Typography variant="body1">{caseData.investigator}</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Organization</Typography>
              <Typography variant="body1">{caseData.organization}</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Evidence Count</Typography>
              <Typography variant="body1">{caseData.evidence?.length || 0}</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Findings</Typography>
              <Typography variant="body1">{caseData.findings?.length || 0}</Typography>
            </Box>
          </Box>
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary">Endpoints</Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
              {(caseData.endpoints || []).map((ep) => (
                <Chip key={ep} label={ep} size="small" variant="outlined" />
              ))}
            </Box>
          </Box>
        </Paper>
      ) : (
        <Typography color="text.secondary">Loading case data...</Typography>
      )}
    </Box>
  );
}
