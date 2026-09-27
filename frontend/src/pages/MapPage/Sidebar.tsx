import React from 'react';
import { mockTrainData } from '../../data/mapMockData';
import { X, Clock, Navigation } from 'lucide-react';

interface SidebarProps {
  trainId: string | null;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ trainId, onClose }) => {
  if (!trainId) return null;

  // In a real app, we'd fetch data based on trainId. For now, just use mockTrainData.
  const train = trainId === mockTrainData.id ? mockTrainData : mockTrainData; // fallback to mock main train

  return (
    <div
      className="glass-panel"
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '380px',
        height: '100vh',
        zIndex: 20,
        display: 'flex',
        flexDirection: 'column',
        borderLeft: 'none',
        borderTop: 'none',
        borderBottom: 'none',
        borderRadius: '0 16px 16px 0',
        transition: 'transform 0.3s ease',
        transform: trainId ? 'translateX(0)' : 'translateX(-100%)',
      }}
    >
      {/* Header */}
      <div style={{ padding: '20px', borderBottom: 'var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 600, margin: 0 }}>{train.number} {train.name}</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--danger-color)' }}>
              <Clock size={14} />
              {train.delayMinutes}M LATE
            </span>
            <span>•</span>
            <span style={{ color: 'var(--success-color)' }}>{train.status}</span>
          </div>
        </div>
        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>
          <X size={24} />
        </button>
      </div>

      {/* Schedule List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 20px' }}>
        <div style={{ position: 'relative', marginTop: '20px' }}>
          {/* Vertical Line */}
          <div style={{ position: 'absolute', left: '11px', top: '10px', bottom: '20px', width: '2px', backgroundColor: 'var(--panel-border)', zIndex: 0 }} />
          
          {train.route.map((station, index) => {
            const isCurrent = index === train.currentStationIndex;
            return (
              <div key={station.code} style={{ display: 'flex', alignItems: 'flex-start', marginBottom: '24px', position: 'relative', zIndex: 1 }}>
                
                {/* Node */}
                <div style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  backgroundColor: station.isPassed ? 'var(--success-color)' : 'var(--panel-bg)',
                  border: `2px solid ${isCurrent ? 'var(--accent-color)' : station.isPassed ? 'var(--success-color)' : 'var(--text-secondary)'}`,
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  marginRight: '16px',
                  flexShrink: 0,
                  boxShadow: isCurrent ? '0 0 10px var(--accent-color)' : 'none'
                }}>
                  {isCurrent && <Navigation size={12} fill="var(--accent-color)" color="var(--accent-color)" />}
                </div>

                {/* Info */}
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                    <h3 style={{ fontSize: '16px', fontWeight: 500, margin: 0, color: isCurrent ? 'var(--accent-color)' : 'var(--text-primary)' }}>
                      {station.name}
                    </h3>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '14px', fontWeight: 500 }}>{station.arrival}</div>
                      <div style={{ fontSize: '12px', color: 'var(--danger-color)' }}>{station.departure}</div>
                    </div>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    {station.code} • {station.distance} km • {station.platform}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
