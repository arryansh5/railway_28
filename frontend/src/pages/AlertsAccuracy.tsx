import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import { AlertTriangle, Info, CheckCircle2, TrendingUp } from 'lucide-react';
import { mockAlerts } from '../data/mockData';

const accuracyData = [
  { date: '25 Aug', accuracy: 88 },
  { date: '26 Aug', accuracy: 89 },
  { date: '27 Aug', accuracy: 92 },
  { date: '28 Aug', accuracy: 91 },
  { date: '29 Aug', accuracy: 93 },
  { date: '30 Aug', accuracy: 90 },
  { date: '31 Aug', accuracy: 91.2 },
];

export const AlertsAccuracy: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-text">Alerts & System Accuracy</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Operational Alerts */}
        <div className="bg-background border border-border rounded-xl p-6 flex flex-col">
          <div className="flex items-center gap-2 mb-6">
            <AlertTriangle className="w-6 h-6 text-warning" aria-hidden="true" />
            <h3 className="text-lg font-bold text-text uppercase tracking-wider">System Alerts</h3>
          </div>
          
          <div className="space-y-4 flex-1">
            {mockAlerts.map(alert => (
              <div key={alert.id} className="p-4 rounded-xl border border-border bg-surface flex gap-4">
                <div className={`p-2 rounded-lg shrink-0 h-min ${
                  alert.level === 'CRITICAL' ? 'bg-criticalBg text-critical' :
                  alert.level === 'WARNING' ? 'bg-warningBg text-warning' : 'bg-primary/10 text-primary'
                }`}>
                  {alert.level === 'CRITICAL' ? <AlertTriangle className="w-6 h-6" /> :
                   alert.level === 'WARNING' ? <AlertTriangle className="w-6 h-6" /> :
                   <Info className="w-6 h-6" />}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-start">
                    <h4 className="font-bold text-text">{alert.title}</h4>
                    <span className="text-xs font-medium text-textMuted">{alert.time}</span>
                  </div>
                  <p className="text-sm text-textMuted mt-1">{alert.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Model Accuracy & Metrics */}
        <div className="bg-background border border-border rounded-xl p-6 flex flex-col">
          <div className="flex items-center gap-2 mb-6">
            <TrendingUp className="w-6 h-6 text-primary" aria-hidden="true" />
            <h3 className="text-lg font-bold text-text uppercase tracking-wider">Model Accuracy Trend</h3>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
            <div className="p-4 rounded-lg bg-surface border border-border text-center">
              <div className="text-xs text-textMuted uppercase tracking-wider font-semibold mb-1">MAE</div>
              <div className="text-xl font-bold text-text">2.9 <span className="text-sm font-normal text-textMuted">min</span></div>
            </div>
            <div className="p-4 rounded-lg bg-surface border border-border text-center">
              <div className="text-xs text-textMuted uppercase tracking-wider font-semibold mb-1">RMSE</div>
              <div className="text-xl font-bold text-text">4.3 <span className="text-sm font-normal text-textMuted">min</span></div>
            </div>
            <div className="p-4 rounded-lg bg-surface border border-border text-center">
              <div className="text-xs text-textMuted uppercase tracking-wider font-semibold mb-1">MAPE</div>
              <div className="text-xl font-bold text-text">5.2%</div>
            </div>
            <div className="p-4 rounded-lg bg-successBg border border-success/20 text-center">
              <div className="text-xs text-success uppercase tracking-wider font-bold mb-1">Accuracy</div>
              <div className="text-xl font-bold text-success flex justify-center items-center gap-1">
                91.2% <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
          </div>

          <div className="h-[250px] w-full mt-auto">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={accuracyData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorAccuracy" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} dy={10} />
                <YAxis domain={[80, 100]} stroke="#64748b" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} dx={-10} tickFormatter={(val) => `${val}%`} />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px' }}
                  formatter={(value: any) => [`${value}%`, 'Accuracy']}
                />
                <Area type="monotone" dataKey="accuracy" stroke="#2563eb" strokeWidth={3} fillOpacity={1} fill="url(#colorAccuracy)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          
          <div className="mt-4 pt-4 border-t border-border flex justify-between items-center text-xs text-textMuted">
            <span>Last Model Update: 31 Aug 2024 02:15 AM</span>
            <span>Version: v2.3.1</span>
          </div>
        </div>
      </div>
    </div>
  );
};
