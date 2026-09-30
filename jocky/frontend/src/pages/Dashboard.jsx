import React, { useEffect, useState } from 'react';
import { Typography, Grid, Paper, Box, Chip } from '@mui/material';
import StatusPanel from '../components/StatusPanel';
import { api, connectWebSocket } from '../api/client';

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [wsEvents, setWsEvents] = useState([]);
  const caseId = 'OP-FALCON-01';

  useEffect(() => {
    api.health().then(res => setHealth(res.data)).catch(() => {});
    const ws = connectWebSocket(caseId, (event) => {
      setWsEvents(prev => [...prev.slice(-50), event]);
    });
    return () => ws.close();
  }, []);

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, color: 'primary.main' }}>
        Investigation Dashboard
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">Case</Typography>
            <Typography variant="h5">{caseId}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">Backend</Typography>
            <Chip
              label={health ? 'CONNECTED' : 'OFFLINE'}
              color={health ? 'success' : 'error'}
              size="small"
            />
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">Endpoints</Typography>
            <Typography variant="h5">{health?.endpoints_connected || 0}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <StatusPanel events={wsEvents} />
        </Grid>
      </Grid>
    </Box>
  );
}
