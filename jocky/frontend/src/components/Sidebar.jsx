import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';

const LINKS = [
  { to: '/dashboard',  label: 'Dashboard',    icon: '⬡' },
  { to: '/editor',     label: 'Editor',        icon: '✎' },
  { to: '/endpoints',  label: 'Endpoints',     icon: '⬢' },
  { to: '/graph',      label: 'Evidence Graph',icon: '◈' },
  { to: '/timeline',   label: 'Timeline',      icon: '◷' },
  { to: '/findings',   label: 'Findings',      icon: '◉' },
  { to: '/kernel',     label: 'Kernel State',  icon: '⬖' },
  { to: '/blockchain', label: 'Blockchain',    icon: '⛓' },
  { to: '/reports',    label: 'Reports',       icon: '⊞' },
];

export default function Sidebar() {
  const navigate = useNavigate();

  function logout() {
    localStorage.removeItem('jocky_token');
    navigate('/login');
  }

  return (
    <aside className="fixed left-0 top-0 h-full w-56 bg-gray-950 border-r border-gray-800 flex flex-col z-10">
      {/* Header */}
      <div className="px-4 py-4 border-b border-gray-800">
        <div className="text-green-400 font-bold text-lg tracking-widest">JOCKY</div>
        <div className="text-gray-500 text-xs mt-0.5">OP-FALCON-01</div>
        <div className="flex items-center gap-1 mt-1">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse inline-block"></span>
          <span className="text-green-400 text-xs">ACTIVE</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-2 overflow-y-auto">
        {LINKS.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2 text-sm transition-colors ${
                isActive
                  ? 'bg-gray-800 text-green-400 border-r-2 border-green-400'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
              }`
            }
          >
            <span className="text-base w-5 text-center">{icon}</span>
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-gray-800">
        <div className="text-gray-600 text-xs mb-2">SIH 2026 · PS 26148 · NTRO</div>
        <button
          onClick={logout}
          className="text-xs text-gray-500 hover:text-red-400 transition-colors"
        >
          ⏻ Logout
        </button>
      </div>
    </aside>
  );
}
