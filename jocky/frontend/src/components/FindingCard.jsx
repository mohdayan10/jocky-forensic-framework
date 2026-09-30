import React from 'react';
import { Card, CardContent, Typography, Chip, Box, Stack } from '@mui/material';

const severityColor = {
  CRITICAL: '#ff1744',
  HIGH:     '#ff9100',
  MEDIUM:   '#ffc400',
  LOW:      '#00e676',
};

export default function FindingCard({ finding }) {
  return (
    <Card sx={{ mb: 2, border: `1px solid ${severityColor[finding.severity] || '#333'}` }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="h6" sx={{ fontFamily: 'monospace' }}>
            {finding.finding_id}
          </Typography>
          <Stack direction="row" spacing={1}>
            <Chip
              label={finding.severity}
              size="small"
              sx={{ bgcolor: severityColor[finding.severity], color: '#000', fontWeight: 700 }}
            />
            <Chip label={`Confidence: ${finding.confidence}`} size="small" variant="outlined" />
          </Stack>
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Rules fired: {finding.rules_fired?.length || 0}
        </Typography>

        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
          {(finding.rules_fired || []).map((rule) => (
            <Chip key={rule} label={rule} size="small" variant="outlined" />
          ))}
        </Box>

        <Typography variant="caption" sx={{ mt: 1, display: 'block', color: 'text.secondary' }}>
          Evidence: {(finding.evidence_ids || []).join(', ')}
        </Typography>
      </CardContent>
    </Card>
  );
}
