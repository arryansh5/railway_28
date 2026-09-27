import React from 'react';
import { Search, Menu, X } from 'lucide-react';

export const SearchBar: React.FC = () => {
  return (
    <div
      className="glass-panel"
      style={{
        position: 'absolute',
        top: '20px',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '400px',
        maxWidth: '90vw',
        display: 'flex',
        alignItems: 'center',
        padding: '8px 16px',
        zIndex: 10,
      }}
    >
      <Menu size={20} style={{ color: 'var(--text-secondary)', marginRight: '12px', cursor: 'pointer' }} />
      <input
        type="text"
        placeholder="Search Train or Station"
        style={{
          flex: 1,
          background: 'transparent',
          border: 'none',
          color: 'var(--text-primary)',
          fontSize: '16px',
          outline: 'none',
        }}
      />
      <Search size={20} style={{ color: 'var(--text-secondary)', cursor: 'pointer' }} />
    </div>
  );
};
