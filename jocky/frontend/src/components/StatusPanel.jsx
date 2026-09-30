import React from 'react';
import { Paper, Typography, Box, Chip, LinearProgress } from '@mui/material';

export default function StatusPanel({ events = [] }) {
  const statusColor = (status) => {
    switch (status) {
      case 'COLLECTING': return 'warning';
      case 'COMPLETE':   return 'success';
      case 'ERROR':      return 'error';
      default:           return 'default';
    }
  };

  return (
    <Paper sx={{ p: 2, bgcolor: 'background.paper' }}>
      <Typography variant="h6" sx={{ mb: 1, color: 'primary.main' }}>
        Live Status
      </Typography>
      {events.length === 0 && (
        <Typography variant="body2" color="text.secondary">
          Waiting for agent status updates...
        </Typography>
      )}
      {events.map((event, i) => (
        <Box key={i} sx={{ mb: 1 }}>
          {event.type === 'AGENT_STATUS' && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <Typography variant="body2">{event.host_id}</Typography>
              <Chip label={event.status} size="small" color={statusColor(event.status)} />
              {event.artifact_count && (
                <Typography variant="caption" color="text.secondary">
                  {event.artifact_count} artifacts
                </Typography>
              )}
            </Box>
          )}
          {event.type === 'FINDING_RAISED' && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip label="FINDING" size="small" color="error" />
              <Typography variant="body2">{event.finding_id}</Typography>
              <Chip label={event.severity} size="small" color="error" variant="outlined" />
            </Box>
          )}
          {event.status === 'COLLECTING' && <LinearProgress color="warning" sx={{ mt: 0.5 }} />}
        </Box>
      ))}
    </Paper>
  );
}
