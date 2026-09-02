import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, Train, Info, Activity, AlertTriangle, LogOut } from 'lucide-react';

import { useWebSocket } from '../context/WebSocketContext';

const navItems = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  // { name: 'Live Trains', path: '/trains', icon: Train },
  // { name: 'Train Details', path: '/details', icon: Info },
  { name: 'Predictions', path: '/predictions', icon: Activity },
  // { name: 'Alerts', path: '/alerts', icon: AlertTriangle },
];

export const Layout: React.FC = () => {
  const { isConnected } = useWebSocket();
  return (
    <div className="flex h-screen bg-surface">
      {/* Sidebar */}
      {/* <aside className="w-64 bg-background border-r border-border flex flex-col h-full" aria-label="Sidebar Navigation">
        <div className="p-6 flex items-center gap-3 border-b border-border">
          <Train className="w-8 h-8 text-primary" aria-hidden="true" />
          <div>
            <h1 className="font-bold text-xl text-text leading-tight">RAIL-AI</h1>
            <p className="text-xs text-textMuted uppercase font-semibold tracking-wider">ETA System</p>
          </div>
        </div>
        
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-primary ${
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-text hover:bg-surface hover:text-primary'
                }`
              }
            >
              <item.icon className="w-5 h-5" aria-hidden="true" />
              {item.name}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-border">
          <button className="flex items-center gap-3 px-4 py-3 w-full rounded-lg font-medium text-text hover:bg-criticalBg hover:text-critical transition-colors focus:outline-none focus:ring-2 focus:ring-critical">
            <LogOut className="w-5 h-5" aria-hidden="true" />
            Logout
          </button>
        </div>
      </aside> */}

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Topbar */}
        <header className="h-16 bg-background border-b border-border flex items-center justify-between px-8" aria-label="Top Bar">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 pr-2">
              <Train className="w-6 h-6 text-primary" aria-hidden="true" />
              <div>
                <h1 className="font-bold text-lg text-text tracking-wide">Station Controller</h1>
              </div>
            </div>
            
            <div className="h-6 w-px bg-border"></div>

            <div className="flex items-center gap-4 text-sm font-medium text-textMuted">
            <span>Station: New Delhi</span>
            <span className="w-1 h-1 rounded-full bg-border" aria-hidden="true"></span>
            <span>{new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })} | {new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}</span>
            <span className="w-1 h-1 rounded-full bg-border" aria-hidden="true"></span>
            <div className={`flex items-center gap-2 ${isConnected ? 'text-success' : 'text-warning'}`}>
              <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-success' : 'bg-warning'} ${isConnected ? 'animate-pulse' : ''}`} aria-hidden="true"></span>
              {isConnected ? 'LIVE DATA CONNECTED' : 'CONNECTING...'}
            </div>
            </div>
          </div>
          
          {/* <div className="flex items-center gap-6">
            <button className="relative text-textMuted hover:text-text focus:outline-none focus:ring-2 focus:ring-primary rounded-full p-1" aria-label="Notifications">
              <AlertTriangle className="w-5 h-5" />
              <span className="absolute top-0 right-0 w-2 h-2 bg-critical rounded-full border border-background"></span>
            </button>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-surface border border-border flex items-center justify-center font-bold text-primary" aria-hidden="true">
                SC
              </div>
              <span className="font-medium text-sm text-text">Station Controller</span>
            </div>
          </div> */}
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-8" id="main-content" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};
