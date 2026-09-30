import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline, Box } from '@mui/material';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Editor from './pages/Editor';
import EvidenceGraph from './pages/EvidenceGraph';
import Timeline from './pages/Timeline';
import Findings from './pages/Findings';
import KernelState from './pages/KernelState';
import Blockchain from './pages/Blockchain';
import Reports from './pages/Reports';
import Endpoints from './pages/Endpoints';
import Login from './pages/Login';
import CaseManager from './pages/CaseManager';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary:   { main: '#00e676' },
    secondary: { main: '#ff9100' },
    error:     { main: '#ff1744' },
    background: { default: '#0a0e17', paper: '#111827' },
  },
  typography: { fontFamily: '"JetBrains Mono", "Fira Code", monospace' },
});

const DRAWER_WIDTH = 240;

export default function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <BrowserRouter>
        <Box sx={{ display: 'flex' }}>
          <Sidebar width={DRAWER_WIDTH} />
          <Box component="main" sx={{ flexGrow: 1, p: 3, ml: `${DRAWER_WIDTH}px`, minHeight: '100vh' }}>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/login" element={<Login />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/cases" element={<CaseManager />} />
              <Route path="/editor" element={<Editor />} />
              <Route path="/endpoints" element={<Endpoints />} />
              <Route path="/graph" element={<EvidenceGraph />} />
              <Route path="/timeline" element={<Timeline />} />
              <Route path="/findings" element={<Findings />} />
              <Route path="/kernel" element={<KernelState />} />
              <Route path="/blockchain" element={<Blockchain />} />
              <Route path="/reports" element={<Reports />} />
            </Routes>
          </Box>
        </Box>
      </BrowserRouter>
    </ThemeProvider>
  );
}
