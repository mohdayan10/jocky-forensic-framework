import React, { useState } from 'react';
import { Paper, Typography, TextField, Button, Box, Chip, CircularProgress } from '@mui/material';
import { api } from '../api/client';

export default function AiAssistant({ findingId }) {
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleExplain = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.explain(findingId);
      setResponse(res.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to get AI explanation');
    }
    setLoading(false);
  };

  return (
    <Paper sx={{ p: 2, bgcolor: 'background.paper' }}>
      <Typography variant="h6" sx={{ color: 'primary.main', mb: 1 }}>
        AI Forensic Assistant
      </Typography>

      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
        <TextField
          size="small"
          value={findingId || ''}
          label="Finding ID"
          disabled
          sx={{ flexGrow: 1 }}
        />
        <Button
          variant="contained"
          onClick={handleExplain}
          disabled={!findingId || loading}
        >
          {loading ? <CircularProgress size={20} /> : 'Explain'}
        </Button>
      </Box>

      {error && (
        <Typography color="error" variant="body2" sx={{ mb: 1 }}>
          {error}
        </Typography>
      )}

      {response && (
        <>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mb: 2, lineHeight: 1.6 }}>
            {response.explanation}
          </Typography>

          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            <Typography variant="caption" sx={{ mr: 1 }}>Citations:</Typography>
            {(response.cited_ids || []).map((id) => (
              <Chip
                key={id}
                label={id}
                size="small"
                color={response.valid_ids?.includes(id) ? 'success' : 'error'}
              />
            ))}
          </Box>

          <Chip
            label={response.validated ? 'VALIDATED' : 'REJECTED'}
            color={response.validated ? 'success' : 'error'}
            sx={{ mt: 1 }}
          />
        </>
      )}
    </Paper>
  );
}
