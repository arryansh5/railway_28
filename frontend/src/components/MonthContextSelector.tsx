import React, { useEffect, useState } from 'react';
import { useWebSocket, type HistoricalContext } from '../context/WebSocketContext';
import { Calendar } from 'lucide-react';
import { getApiUrl } from '../config/api';

const MONTHS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

export const MonthContextSelector: React.FC<{ simTime?: string }> = ({ simTime = '06:45:00' }) => {
  const { selectedMonth, setMonth, isConnected } = useWebSocket();
  const [contextData, setContextData] = useState<HistoricalContext | null>(null);

  useEffect(() => {
    const fetchContext = async () => {
      try {
        const url = getApiUrl(`/api/historical-context?month=${selectedMonth}&route=dehradun`);
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          setContextData(data);
        }
      } catch (err) {
        console.error('Error fetching historical context:', err);
      }
    };

    fetchContext();
  }, [selectedMonth]);

  const handleMonthChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setMonth(e.target.value);
  };

  const getSeasonBadge = (season?: string) => {
    switch (season) {
      case 'Monsoon':
        return { text: 'Monsoon (Heavy Rain Caution)', color: 'bg-primary/10 text-primary border-primary/20', icon: '🌧️' };
      case 'Winter/Fog':
        return { text: 'Winter (Morning Fog Protocol)', color: 'bg-criticalBg text-critical border-critical/20', icon: '❄️' };
      case 'Summer':
        return { text: 'Summer (High Speed Corridor)', color: 'bg-warningBg text-warning border-warning/20', icon: '☀️' };
      case 'Post-Monsoon':
      case 'Autumn':
      default:
        return { text: 'Autumn (Clear Line Speed)', color: 'bg-successBg text-success border-success/20', icon: '🍂' };
    }
  };

  const seasonBadge = getSeasonBadge(contextData?.season);

  return (
    <div className="bg-background border border-border rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-4 shadow-sm">
      {/* Left: Month Selection & Active Season Badge */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-text font-bold text-xs">
          <Calendar className="w-4 h-4 text-primary" />
          <span>Simulation Month:</span>
        </div>

        <select
          value={selectedMonth}
          onChange={handleMonthChange}
          className="bg-surface text-text font-semibold text-xs rounded-lg px-3 py-1.5 border border-border hover:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition-colors cursor-pointer"
        >
          {MONTHS.map((m) => (
            <option key={m} value={m} className="bg-background text-text">
              {m} {['December', 'January', 'February'].includes(m) ? '❄️' : ['June', 'July', 'August', 'September'].includes(m) ? '🌧️' : '☀️'}
            </option>
          ))}
        </select>

        {contextData && (
          <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold border ${seasonBadge.color}`}>
            <span>{seasonBadge.icon}</span>
            <span>{seasonBadge.text}</span>
          </span>
        )}
      </div>

      {/* Right: 30s Live Simulation Pulse */}
      <div className="flex items-center gap-2 text-xs bg-surface px-3 py-1.5 rounded-lg border border-border">
        <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-success animate-pulse' : 'bg-warning'}`}></span>
        <span className="text-textMuted">30s Cycle:</span>
        <span className="font-mono font-bold text-primary">{simTime}</span>
      </div>
    </div>
  );
};
