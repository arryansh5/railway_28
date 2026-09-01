import React from 'react';
import { Train, Clock, AlertTriangle, Activity, CheckCircle2, Info } from 'lucide-react';
import { mockTrains, mockAlerts } from '../data/mockData';

const StatCard: React.FC<{ title: string, value: string | number, subValue: string, icon: any, colorClass: string, bgClass: string }> = ({ title, value, subValue, icon: Icon, colorClass, bgClass }) => (
  <div className={`p-6 rounded-xl border border-border bg-background flex items-center gap-4`}>
    <div className={`p-4 rounded-lg ${bgClass} ${colorClass}`}>
      <Icon className="w-8 h-8" aria-hidden="true" />
    </div>
    <div>
      <h3 className="text-sm font-semibold text-textMuted uppercase tracking-wider">{title}</h3>
      <div className="text-2xl font-bold text-text mt-1">{value}</div>
      <p className="text-sm text-textMuted mt-1">{subValue}</p>
    </div>
  </div>
);

const RouteProgress: React.FC<{ from: string, to: string, onTime: boolean, trains: number, avgDelay: number, onTimePct: number }> = ({ from, to, onTime, trains, avgDelay, onTimePct }) => (
  <div className="bg-background border border-border p-5 rounded-xl">
    <div className="flex justify-between items-center mb-4">
      <h4 className="font-semibold text-text flex items-center gap-2">
        {from} <span className="text-textMuted">→</span> {to}
      </h4>
      <span className={`px-2 py-1 text-xs font-bold rounded-md ${onTime ? 'bg-successBg text-success' : 'bg-warningBg text-warning'}`}>
        {onTime ? 'On Time' : 'Delayed'}
      </span>
    </div>
    <div className="relative w-full h-2 bg-border rounded-full mb-6">
      <div className={`absolute top-0 left-0 h-full rounded-full ${onTime ? 'bg-success' : 'bg-warning'} w-2/3`}></div>
      <div className="absolute top-1/2 left-0 w-3 h-3 -translate-y-1/2 bg-background border-2 border-text rounded-full"></div>
      <div className="absolute top-1/2 left-2/3 w-3 h-3 -translate-y-1/2 bg-background border-2 border-text rounded-full"></div>
      <div className="absolute top-1/2 right-0 w-3 h-3 -translate-y-1/2 bg-background border-2 border-text rounded-full"></div>
    </div>
    <div className="grid grid-cols-3 gap-4 text-center">
      <div>
        <div className="text-sm font-bold text-text">{trains}</div>
        <div className="text-xs text-textMuted">Trains</div>
      </div>
      <div>
        <div className={`text-sm font-bold ${avgDelay > 5 ? 'text-critical' : 'text-success'}`}>{avgDelay > 0 ? '+' : ''}{avgDelay} min</div>
        <div className="text-xs text-textMuted">Avg Delay</div>
      </div>
      <div>
        <div className="text-sm font-bold text-success">{onTimePct}%</div>
        <div className="text-xs text-textMuted">On Time</div>
      </div>
    </div>
  </div>
);

export const Dashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-text">Overview</h2>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-6">
        <StatCard title="Active Trains" value="27" subValue="All Routes" icon={Train} colorClass="text-primary" bgClass="bg-primary/10" />
        <StatCard title="On Time" value="16" subValue="59.3%" icon={CheckCircle2} colorClass="text-success" bgClass="bg-successBg" />
        <StatCard title="Delayed" value="8" subValue="29.6%" icon={Clock} colorClass="text-warning" bgClass="bg-warningBg" />
        <StatCard title="Critical Delay" value="3" subValue="11.1%" icon={AlertTriangle} colorClass="text-critical" bgClass="bg-criticalBg" />
        <StatCard title="ETA Accuracy" value="91.2%" subValue="Last 24h" icon={Activity} colorClass="text-primary" bgClass="bg-primary/10" />
      </div>

      {/* Route Summaries */}
      <div>
        <h3 className="text-lg font-bold text-text mb-4 uppercase tracking-wider">Route Summary</h3>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <RouteProgress from="Delhi" to="Dehradun" onTime={true} trains={9} avgDelay={4.2} onTimePct={66.7} />
          <RouteProgress from="Delhi" to="Agra" onTime={false} trains={9} avgDelay={9.7} onTimePct={44.4} />
          <RouteProgress from="Delhi" to="Lucknow" onTime={false} trains={9} avgDelay={11.9} onTimePct={33.3} />
        </div>
      </div>

      {/* Live Trains & Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-background border border-border rounded-xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-text uppercase tracking-wider">Live Trains Snapshot</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse" aria-label="Live Trains Table">
              <thead>
                <tr className="border-b border-border text-xs font-semibold text-textMuted uppercase">
                  <th className="pb-3 pr-4">Train</th>
                  <th className="pb-3 px-4">Route</th>
                  <th className="pb-3 px-4">Sched. ETA</th>
                  <th className="pb-3 px-4">AI ETA</th>
                  <th className="pb-3 pl-4 text-right">Status</th>
                </tr>
              </thead>
              <tbody>
                {mockTrains.slice(0, 4).map(train => (
                  <tr key={train.id} className="border-b border-border last:border-0 hover:bg-surface transition-colors">
                    <td className="py-3 pr-4">
                      <div className="font-bold text-text">{train.id}</div>
                      <div className="text-xs text-textMuted">{train.name}</div>
                    </td>
                    <td className="py-3 px-4 text-sm text-text">{train.route}</td>
                    <td className="py-3 px-4 text-sm text-text">{train.scheduledEta}</td>
                    <td className="py-3 px-4 text-sm font-bold text-text">{train.aiEta}</td>
                    <td className="py-3 pl-4 text-right">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border
                        ${train.status === 'ON_TIME' ? 'bg-successBg text-success border-success/20' : 
                          train.status === 'DELAYED' ? 'bg-warningBg text-warning border-warning/20' : 
                          'bg-criticalBg text-critical border-critical/20'}`}>
                        {train.status.replace('_', ' ')}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-background border border-border rounded-xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-text uppercase tracking-wider">Top Alerts</h3>
          </div>
          <div className="space-y-4">
            {mockAlerts.map(alert => (
              <div key={alert.id} className="flex gap-4 items-start pb-4 border-b border-border last:border-0 last:pb-0">
                <div className={`p-2 rounded-lg shrink-0 ${
                  alert.level === 'CRITICAL' ? 'bg-criticalBg text-critical' :
                  alert.level === 'WARNING' ? 'bg-warningBg text-warning' : 'bg-primary/10 text-primary'
                }`}>
                  {alert.level === 'CRITICAL' ? <AlertTriangle className="w-5 h-5" /> :
                   alert.level === 'WARNING' ? <AlertTriangle className="w-5 h-5" /> :
                   <Info className="w-5 h-5" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-start">
                    <h4 className="font-semibold text-text text-sm truncate">{alert.title}</h4>
                    <span className="text-xs text-textMuted ml-2 whitespace-nowrap">{alert.time}</span>
                  </div>
                  <p className="text-xs text-textMuted mt-1">{alert.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
