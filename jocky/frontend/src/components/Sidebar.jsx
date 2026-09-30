import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Drawer, List, ListItemButton, ListItemIcon, ListItemText,
  Typography, Box, Divider,
} from '@mui/material';
import {
  Dashboard, Code, DeviceHub, Timeline, BugReport,
  Memory, VerifiedUser, Description, Dns, Login, FolderOpen,
} from '@mui/icons-material';

const NAV_ITEMS = [
  { path: '/dashboard',  label: 'Dashboard',      icon: <Dashboard /> },
  { path: '/cases',      label: 'Case Manager',   icon: <FolderOpen /> },
  { path: '/editor',     label: 'JOCKY Editor',   icon: <Code /> },
  { path: '/endpoints',  label: 'Endpoints',      icon: <Dns /> },
  { path: '/graph',      label: 'Evidence Graph',  icon: <DeviceHub /> },
  { path: '/timeline',   label: 'Timeline',        icon: <Timeline /> },
  { path: '/findings',   label: 'Findings',        icon: <BugReport /> },
  { path: '/kernel',     label: 'Kernel State',    icon: <Memory /> },
  { path: '/blockchain', label: 'Blockchain',       icon: <VerifiedUser /> },
  { path: '/reports',    label: 'Reports',          icon: <Description /> },
];

export default function Sidebar({ width }) {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width,
        '& .MuiDrawer-paper': {
          width, boxSizing: 'border-box',
          bgcolor: 'background.paper', borderRight: '1px solid #1e293b',
        },
      }}
    >
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="h5" sx={{ color: 'primary.main', fontWeight: 700 }}>
          JOCKY
        </Typography>
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          Forensic Command Console
        </Typography>
      </Box>
      <Divider />
      <List>
        {NAV_ITEMS.map(({ path, label, icon }) => (
          <ListItemButton
            key={path}
            selected={location.pathname === path}
            onClick={() => navigate(path)}
          >
            <ListItemIcon sx={{ color: location.pathname === path ? 'primary.main' : 'text.secondary' }}>
              {icon}
            </ListItemIcon>
            <ListItemText primary={label} />
          </ListItemButton>
        ))}
      </List>
    </Drawer>
  );
}
