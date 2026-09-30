import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Editor from './pages/Editor';
import Endpoints from './pages/Endpoints';
import EvidenceGraph from './pages/EvidenceGraph';
import Timeline from './pages/Timeline';
import Findings from './pages/Findings';
import KernelState from './pages/KernelState';
import Blockchain from './pages/Blockchain';
import Reports from './pages/Reports';

function RequireAuth({ children }) {
  const token = localStorage.getItem('jocky_token');
  return token ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/*" element={
          <RequireAuth>
            <div className="flex h-screen bg-gray-900 overflow-hidden">
              <Sidebar />
              <main className="flex-1 overflow-y-auto p-6 ml-56">
                <Routes>
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/editor" element={<Editor />} />
                  <Route path="/endpoints" element={<Endpoints />} />
                  <Route path="/graph" element={<EvidenceGraph />} />
                  <Route path="/timeline" element={<Timeline />} />
                  <Route path="/findings" element={<Findings />} />
                  <Route path="/kernel" element={<KernelState />} />
                  <Route path="/blockchain" element={<Blockchain />} />
                  <Route path="/reports" element={<Reports />} />
                </Routes>
              </main>
            </div>
          </RequireAuth>
        } />
      </Routes>
    </BrowserRouter>
  );
}
