import React, { useEffect, useState } from 'react';
import { useWebSocket, type HistoricalContext } from '../context/WebSocketContext';
import { Calendar, CloudFog, Activity, MapPin } from 'lucide-react';

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
        const res = await fetch(`http://localhost:8000/api/historical-context?month=${selectedMonth}&route=dehradun`);
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
      case 'Winter/Fog':
        return { text: 'Winter / Fog', icon: '❄️', color: 'text-amber-400 bg-amber-500/10 border-amber-500/20' };
      case 'Monsoon':
        return { text: 'Monsoon', icon: '🌧️', color: 'text-blue-400 bg-blue-500/10 border-blue-500/20' };
      case 'Summer':
        return { text: 'Summer', icon: '☀️', color: 'text-orange-400 bg-orange-500/10 border-orange-500/20' };
      default:
        return { text: 'Autumn / Post-Monsoon', icon: '🍂', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' };
    }
  };

  const seasonBadge = getSeasonBadge(contextData?.season);

  return (
    <div className="bg-background border border-border rounded-xl p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
      {/* Left: Month Selector & Season */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-primary" />
          <span className="text-xs font-bold text-text uppercase tracking-wider">Simulation Month:</span>
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

      {/* Center: Live Calibration Context Pills */}
      {contextData && (
        <div className="flex flex-wrap items-center gap-3 text-xs">
          {/* Fog Prior */}
          <div className="flex items-center gap-1.5 bg-surface px-2.5 py-1 rounded-md border border-border">
            <CloudFog className={`w-3.5 h-3.5 ${contextData.historical_fog_risk > 0.4 ? 'text-warning' : 'text-success'}`} />
            <span className="text-textMuted">Hist. Fog:</span>
            <span className={`font-bold ${contextData.historical_fog_risk > 0.4 ? 'text-warning' : 'text-success'}`}>
              {contextData.historical_fog_risk_pct}%
            </span>
          </div>

          {/* Regional Congestion */}
          <div className="flex items-center gap-1.5 bg-surface px-2.5 py-1 rounded-md border border-border">
            <Activity className="w-3.5 h-3.5 text-primary" />
            <span className="text-textMuted">NR Congestion:</span>
            <span className="font-bold text-text">{contextData.historical_congestion_risk_pct}%</span>
          </div>

          {/* Region */}
          <div className="flex items-center gap-1 bg-surface px-2.5 py-1 rounded-md border border-border text-textMuted">
            <MapPin className="w-3.5 h-3.5 text-textMuted" />
            <span>NR + NCR</span>
          </div>
        </div>
      )}

      {/* Right: 30s Live Simulation Pulse */}
      <div className="flex items-center gap-2 text-xs bg-surface px-3 py-1.5 rounded-lg border border-border">
        <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-success animate-pulse' : 'bg-warning'}`}></span>
        <span className="text-textMuted">30s Cycle:</span>
        <span className="font-mono font-bold text-primary">{simTime}</span>
      </div>
    </div>
  );
};
