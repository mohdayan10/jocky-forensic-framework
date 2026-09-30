import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Demo auth — accept investigator with any non-empty password
    if (username.trim().toLowerCase() === 'investigator' && password.trim().length > 0) {
      localStorage.setItem('jocky_token', 'demo-investigator-token');
      localStorage.setItem('jocky_user', 'investigator');
      navigate('/dashboard');
      return;
    }

    setError('Use username: investigator (any password)');
    setLoading(false);
  }

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="w-96 bg-gray-800 border border-gray-700 rounded-lg p-8">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="text-green-400 text-4xl font-bold tracking-widest mb-1">JOCKY</div>
          <div className="text-gray-400 text-sm">Forensic Command Console</div>
          <div className="text-gray-600 text-xs mt-1">NTRO · Smart India Hackathon 2026</div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-gray-400 text-xs mb-1 uppercase tracking-wider">Username</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-gray-200 text-sm focus:outline-none focus:border-green-500 font-mono"
              placeholder="investigator"
              autoComplete="username"
            />
          </div>
          <div>
            <label className="block text-gray-400 text-xs mb-1 uppercase tracking-wider">Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-gray-200 text-sm focus:outline-none focus:border-green-500 font-mono"
              placeholder="••••••••"
              autoComplete="current-password"
            />
          </div>

          {error && (
            <div className="text-red-400 text-xs border border-red-800 bg-red-950 rounded px-3 py-2">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 hover:bg-green-500 disabled:bg-gray-700 text-gray-900 font-bold py-2 rounded text-sm transition-colors"
          >
            {loading ? 'Authenticating...' : 'Authenticate'}
          </button>
        </form>

        <div className="text-center mt-4 text-gray-600 text-xs">
          username: investigator · any password
        </div>
      </div>
    </div>
  );
}
