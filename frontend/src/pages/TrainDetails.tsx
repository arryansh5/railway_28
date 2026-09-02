import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts';
import { Train as TrainIcon } from 'lucide-react';
import { mockEtaTrend } from '../data/mockData';
import { useWebSocket } from '../context/WebSocketContext';

export const TrainDetails: React.FC = () => {
  const { liveTrains } = useWebSocket();
  const train = liveTrains.find(t => t.id === '12430') || liveTrains[0]; 

  if (!train) return <div className="p-8 text-center text-textMuted">Loading train details...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-text">Train Details</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Train Info & Timeline */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-background border border-border rounded-xl p-6">
            <div className="flex items-center gap-4 mb-6">
              <div className="p-3 bg-criticalBg text-critical rounded-lg">
                <TrainIcon className="w-8 h-8" aria-hidden="true" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-text">{train.id}</h3>
                <p className="text-textMuted">{train.name}</p>
              </div>
              <div className="ml-auto">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border bg-criticalBg text-critical border-critical/20">
                  {train.status.replace('_', ' ')}
                </span>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex justify-between items-center py-3 border-b border-border">
                <span className="text-textMuted">Route</span>
                <span className="font-semibold text-text">{train.route}</span>
              </div>
              <div className="flex justify-between items-center py-3 border-b border-border">
                <span className="text-textMuted">Current Location</span>
                <span className="font-semibold text-text">{train.currentLocation}</span>
              </div>
              <div className="flex justify-between items-center py-3 border-b border-border">
                <span className="text-textMuted">Scheduled ETA</span>
                <span className="font-semibold text-text">{train.scheduledEta}</span>
              </div>
              <div className="flex justify-between items-center py-3 border-b border-border">
                <span className="text-textMuted">AI ETA</span>
                <span className="font-bold text-critical">{train.aiEta}</span>
              </div>
              <div className="flex justify-between items-center py-3">
                <span className="text-textMuted">Prediction Confidence</span>
                <span className="font-bold text-text">{train.confidence}%</span>
              </div>
            </div>
          </div>

          <div className="bg-background border border-border rounded-xl p-6">
            <h3 className="text-lg font-bold text-text mb-6">Journey Timeline</h3>
            <div className="relative border-l-2 border-border ml-3 space-y-8">
              <div className="relative pl-6">
                <span className="absolute -left-2.5 top-1 w-5 h-5 bg-background border-2 border-border rounded-full flex items-center justify-center">
                  <span className="w-2 h-2 bg-textMuted rounded-full"></span>
                </span>
                <h4 className="font-bold text-text">Delhi (Departure)</h4>
                <p className="text-sm text-textMuted mt-1">Departed at 06:00 (On time)</p>
              </div>
              <div className="relative pl-6">
                <span className="absolute -left-2.5 top-1 w-5 h-5 bg-background border-2 border-border rounded-full flex items-center justify-center">
                  <span className="w-2 h-2 bg-textMuted rounded-full"></span>
                </span>
                <h4 className="font-bold text-text">Aligarh Jn</h4>
                <p className="text-sm text-textMuted mt-1">Arrived at 08:30 (+5 min delay)</p>
              </div>
              <div className="relative pl-6">
                <span className="absolute -left-2.5 top-1 w-5 h-5 bg-background border-2 border-primary rounded-full flex items-center justify-center animate-pulse">
                  <span className="w-2 h-2 bg-primary rounded-full"></span>
                </span>
                <h4 className="font-bold text-primary">Kanpur Central (Current)</h4>
                <p className="text-sm text-textMuted mt-1">Arrived at 10:20 (+16 min delay)</p>
              </div>
              <div className="relative pl-6">
                <span className="absolute -left-2.5 top-1 w-5 h-5 bg-background border-2 border-border rounded-full flex items-center justify-center"></span>
                <h4 className="font-bold text-textMuted">Lucknow (Destination)</h4>
                <p className="text-sm text-textMuted mt-1">Scheduled: 12:10 | AI ETA: 12:26</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - ETA Trend Chart */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-background border border-border rounded-xl p-6 h-[400px]">
            <h3 className="text-lg font-bold text-text mb-6">ETA Trend & History</h3>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mockEtaTrend} margin={{ top: 5, right: 30, left: 20, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="time" stroke="#64748b" tick={{ fill: '#64748b' }} tickLine={false} axisLine={false} dy={10} />
                <YAxis domain={['auto', 'auto']} stroke="#64748b" tick={{ fill: '#64748b' }} tickLine={false} axisLine={false} dx={-10} tickFormatter={(val) => `${Math.floor(val)}:${Math.round((val%1)*60).toString().padStart(2, '0')}`} />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  formatter={(value: any) => [`${Math.floor(value)}:${Math.round((value%1)*60).toString().padStart(2, '0')}`, 'ETA']}
                  labelStyle={{ color: '#0f172a', fontWeight: 'bold', marginBottom: '4px' }}
                />
                <Legend wrapperStyle={{ paddingTop: '20px' }} />
                <Line type="monotone" name="Scheduled ETA" dataKey="scheduled" stroke="#94a3b8" strokeWidth={2} strokeDasharray="5 5" dot={false} />
                <Line type="monotone" name="AI Predicted ETA" dataKey="ai" stroke="#2563eb" strokeWidth={3} dot={{ r: 4, fill: '#2563eb', strokeWidth: 2, stroke: '#ffffff' }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          
          <div className="bg-background border border-border rounded-xl p-6 flex flex-col items-center justify-center text-center">
            <h3 className="text-lg font-bold text-text mb-2">Want to know why?</h3>
            <p className="text-textMuted mb-4">View the detailed breakdown of factors influencing this AI prediction.</p>
            <a href="/predictions" className="px-6 py-2 bg-primary text-white rounded-lg font-medium hover:bg-primaryHover transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2">
              View AI Explanation
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
