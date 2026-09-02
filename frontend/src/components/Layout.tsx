import React from 'react';
import { Outlet } from 'react-router-dom';
import { Train } from 'lucide-react';
import { useWebSocket } from '../context/WebSocketContext';

export const Layout: React.FC = () => {
  const { isConnected } = useWebSocket();
  return (
    <div className="flex h-screen bg-surface">
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
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-8" id="main-content" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};
