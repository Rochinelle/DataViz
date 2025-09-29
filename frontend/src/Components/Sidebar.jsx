// src/components/Sidebar.jsx
import React from 'react';
import { NavLink } from 'react-router-dom';
import { BarChart3, Database, PieChart, Settings } from 'lucide-react';

const Sidebar = () => {
  const navItems = [
    { path: '/dashboard', icon: BarChart3, label: 'Dashboard' },
    { path: '/data-table', icon: Database, label: 'Data Table' },
    { path: '/visualizations', icon: PieChart, label: 'Visualizations' },
    { path: '/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <div className="sidebar">
      <nav className="sidebar-nav">
        {navItems.map(({ path, icon: Icon, label }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) => 
              `nav-link ${isActive ? 'nav-link-active' : ''}`
            }
          >
            <Icon size={20} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
};

export default Sidebar;