import React from 'react';
import { Train, Clock, AlertTriangle, Activity, CheckCircle2, X, TrendingUp, BarChart2 } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend } from 'recharts';
import { useWebSocket, type Train as TrainType } from '../context/WebSocketContext';
import { MonthContextSelector } from '../components/MonthContextSelector';

// Time helpers for charts
const parseTime = (timeStr: string) => {
  if (!timeStr) return 0;
  const parts = timeStr.split(':');
  if (parts.length < 2) return 0;
  const h = parseInt(parts[0], 10) || 0;
  const m = parseInt(parts[1], 10) || 0;
  return h * 60 + m;
};

const formatTime = (minutes: number) => {
  const h = Math.floor(minutes / 60) % 24;
  const m = Math.floor(minutes % 60);
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
};

const RouteModal: React.FC<{ routeName: string; trains: TrainType[]; onClose: () => void }> = ({ routeName, trains, onClose }) => {
  if (!routeName) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-background border border-border rounded-xl w-full max-w-6xl shadow-2xl max-h-[92vh] flex flex-col overflow-hidden text-text">
        
        {/* Modal Header */}
        <div className="p-5 border-b border-border flex justify-between items-center bg-surface">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 text-primary border border-primary/20">
              <Train className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-text flex items-center gap-2">
                Route Details: {routeName}
              </h2>
              <p className="text-xs text-textMuted">
                Live 30-Second Closed-Loop Telemetry & AI Prediction Stream
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-border rounded-lg text-textMuted hover:text-text transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {trains.length === 0 ? (
            <div className="text-center text-textMuted py-12 bg-surface/40 rounded-xl border border-border">
              No active trains on this route right now.
            </div>
          ) : (
            trains.map(train => {
              const timelineData = (train.timeline || []).map((st: any) => ({
                name: st.stationCode,
                stationName: st.stationName,
                scheduledMin: parseTime(st.scheduled),
                predictedMin: parseTime(st.predicted),
                scheduled: st.scheduled,
                predicted: st.predicted,
                delay: st.delay
              }));

              return (
                <div key={train.id} className="p-5 border border-border rounded-xl bg-surface shadow-sm space-y-5">
                  
                  {/* Train Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <h3 className="font-bold text-base text-text">
                        {train.id} - {train.name}
                      </h3>
                      <p className="text-xs text-textMuted flex items-center gap-2 mt-1">
                        <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
                        Currently at: <span className="font-semibold text-text">{train.currentLocation}</span>
                        <span className="text-border">|</span>
                        <span>{train.distanceRemaining.toFixed(1)} km to go</span>
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2.5 py-1 text-xs font-bold rounded-full border ${
                        train.status === 'ON_TIME'
                          ? 'bg-successBg text-success border-success/20'
                          : train.status === 'DELAYED'
                          ? 'bg-warningBg text-warning border-warning/20'
                          : 'bg-criticalBg text-critical border-critical/20'
                      }`}>
                        {train.status.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                  
                  {/* Key Operational KPI Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-background p-4 rounded-lg border border-border">
                    <div>
                      <div className="text-[11px] text-textMuted uppercase font-semibold">Scheduled ETA</div>
                      <div className="font-bold text-sm text-text mt-0.5">{train.scheduledEta}</div>
                    </div>
                    <div>
                      <div className="text-[11px] text-primary uppercase font-semibold">AI Predicted ETA</div>
                      <div className="font-extrabold text-sm text-primary mt-0.5">{train.aiEta}</div>
                    </div>
                    <div>
                      <div className="text-[11px] text-textMuted uppercase font-semibold">Dynamic Delay</div>
                      <div className={`font-bold text-sm mt-0.5 ${train.delayMin > 0 ? 'text-critical' : 'text-success'}`}>
                        {train.delayMin > 0 ? `+${train.delayMin} min` : 'On Time (0m)'}
                      </div>
                    </div>
                    <div>
                      <div className="text-[11px] text-textMuted uppercase font-semibold">AI Confidence</div>
                      <div className="font-bold text-sm text-success mt-0.5">{train.confidence}%</div>
                    </div>
                  </div>
                  
                  {/* Active Delay / Restriction Alert Banner */}
                  {train.delayReason && train.delayReason !== 'None' && (
                    <div className="p-3 bg-criticalBg border border-critical/20 rounded-lg flex items-start gap-2.5">
                      <AlertTriangle className="w-4 h-4 text-critical shrink-0 mt-0.5" />
                      <div>
                        <div className="text-xs font-bold text-critical uppercase tracking-wider">Delay Factor Identified</div>
                        <div className="text-xs text-critical/90 mt-0.5">{train.delayReason}</div>
                      </div>
                    </div>
                  )}

                  {/* Station Schedule & Timeline */}
                  {train.timeline && train.timeline.length > 0 && (
                    <div className="mt-4 border-t border-border pt-4">
                      <h4 className="text-xs font-bold text-text mb-3 uppercase tracking-wider flex items-center gap-2">
                        <Activity className="w-4 h-4 text-primary" />
                        Station-wise Prediction & Timetable Analysis
                      </h4>

                      <div className="overflow-x-auto rounded-lg border border-border">
                        <table className="w-full text-left text-xs border-collapse whitespace-nowrap">
                          <thead>
                            <tr className="border-b border-border bg-surface text-textMuted uppercase font-semibold text-[11px]">
                              <th className="py-2.5 px-3">Station</th>
                              <th className="py-2.5 px-3">Scheduled</th>
                              <th className="py-2.5 px-3">AI Predicted</th>
                              <th className="py-2.5 px-3">Delay</th>
                              <th className="py-2.5 px-3">Confidence</th>
                              <th className="py-2.5 px-3">Section Operational Factor</th>
                              <th className="py-2.5 px-3 text-right">Destination ETA</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border bg-background">
                            {(train.timeline || []).map((st: any, i: number) => {
                              const isTerminal = i === (train.timeline?.length || 0) - 1;
                              const stationConfidence = Math.max(45, (train.confidence || 94) - (i * 2));
                              
                              return (
                                <tr key={i} className="hover:bg-surface transition-colors">
                                  <td className="py-2.5 px-3">
                                    <div className="font-bold text-text flex items-center gap-1.5">
                                      {st.stationName}
                                      {isTerminal && <span className="text-[10px] font-bold px-1.5 py-0.5 bg-primary/10 text-primary rounded border border-primary/20">DEST</span>}
                                    </div>
                                    <div className="text-[10px] text-textMuted">{st.stationCode}</div>
                                  </td>
                                  <td className="py-2.5 px-3 text-text">{st.scheduled}</td>
                                  <td className="py-2.5 px-3 font-bold text-primary">{st.predicted}</td>
                                  <td className="py-2.5 px-3">
                                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold ${
                                      st.delay > 15 ? 'bg-criticalBg text-critical border border-critical/20' :
                                      st.delay > 0 ? 'bg-warningBg text-warning border border-warning/20' :
                                      'bg-successBg text-success border border-success/20'
                                    }`}>
                                      {st.delay > 0 ? `+${st.delay}m` : 'On Time'}
                                    </span>
                                  </td>
                                  <td className="py-2.5 px-3 font-medium text-success flex items-center gap-1">
                                    <CheckCircle2 className="w-3 h-3 text-success" /> {stationConfidence}%
                                  </td>
                                  <td className="py-2.5 px-3 text-[11px] text-textMuted max-w-[240px] truncate" title={st.delayReason || 'Clear'}>
                                    {st.delay > 0 ? (
                                      <span className="flex items-center gap-1 text-critical font-medium">
                                        <AlertTriangle className="w-3 h-3 shrink-0" /> {st.delayReason || train.delayReason || 'Network Delay'}
                                      </span>
                                    ) : (
                                      <span className="text-textMuted">{st.delayReason || 'Normal Cruising'}</span>
                                    )}
                                  </td>
                                  <td className="py-2.5 px-3 text-right font-extrabold text-primary">{train.aiEta}</td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Interactive Visual Graphs */}
                  {timelineData.length > 0 && (
                    <div className="space-y-4 pt-2">
                      <h4 className="text-xs font-bold text-text uppercase tracking-wider flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-primary" />
                        Visual Trajectory & Delay Dynamics
                      </h4>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        
                        {/* Graph 1: Scheduled vs AI Predicted ETA Trend */}
                        <div className="h-64 border border-border rounded-xl bg-background p-4 flex flex-col">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-[11px] font-bold text-text uppercase">ETA Trajectory</span>
                            <span className="text-[10px] text-primary font-mono">Scheduled vs AI Predicted</span>
                          </div>
                          <div className="flex-1 min-h-0">
                            <ResponsiveContainer width="100%" height="100%">
                              <LineChart data={timelineData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.3} />
                                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} dy={5} />
                                <YAxis 
                                  domain={['auto', 'auto']} 
                                  tickFormatter={formatTime} 
                                  tick={{ fontSize: 10, fill: '#64748b' }} 
                                  axisLine={false} 
                                  tickLine={false} 
                                />
                                <RechartsTooltip 
                                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px', color: '#f8fafc', fontSize: '11px' }}
                                  formatter={(val: any, name?: any, props?: any) => {
                                    if (name === 'AI Predicted') return [props?.payload?.predicted || val, name];
                                    if (name === 'Scheduled') return [props?.payload?.scheduled || val, name];
                                    return [val, name || ''];
                                  }}
                                />
                                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '4px' }} />
                                <Line type="monotone" dataKey="predictedMin" stroke="#3b82f6" strokeWidth={2.5} dot={{ r: 3, fill: '#3b82f6' }} activeDot={{ r: 5 }} name="AI Predicted" />
                                <Line type="monotone" dataKey="scheduledMin" stroke="#94a3b8" strokeWidth={1.5} strokeDasharray="4 4" dot={{ r: 2.5, fill: '#94a3b8' }} name="Scheduled" />
                              </LineChart>
                            </ResponsiveContainer>
                          </div>
                        </div>

                        {/* Graph 2: Progressive Station Delay Buildup (mins) */}
                        <div className="h-64 border border-border rounded-xl bg-background p-4 flex flex-col">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-[11px] font-bold text-text uppercase flex items-center gap-1.5">
                              <BarChart2 className="w-3.5 h-3.5 text-critical" />
                              Station Delay Breakdown (mins)
                            </span>
                            <span className="text-[10px] text-critical font-mono">Max +{train.delayMin}m</span>
                          </div>
                          <div className="flex-1 min-h-0">
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart data={timelineData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.3} />
                                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} dy={5} />
                                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                                <RechartsTooltip 
                                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px', color: '#f8fafc', fontSize: '11px' }}
                                  formatter={(val: any) => [`+${val} min`, 'Delay']}
                                />
                                <Bar dataKey="delay" fill="#f43f5e" radius={[4, 4, 0, 0]} name="Delay (min)" maxBarSize={36} />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>

                      </div>
                    </div>
                  )}

                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

const StatCard: React.FC<{ title: string; value: string | number; subValue: string; icon: any; colorClass: string; bgClass: string }> = ({ title, value, subValue, icon: Icon, colorClass, bgClass }) => (
  <div className="p-5 rounded-xl border border-border bg-background flex items-center gap-4 shadow-sm">
    <div className={`p-3.5 rounded-lg ${bgClass} ${colorClass}`}>
      <Icon className="w-7 h-7" aria-hidden="true" />
    </div>
    <div>
      <h3 className="text-xs font-semibold text-textMuted uppercase tracking-wider">{title}</h3>
      <div className="text-xl font-bold text-text mt-0.5">{value}</div>
      <p className="text-xs text-textMuted mt-0.5">{subValue}</p>
    </div>
  </div>
);

const RouteProgress: React.FC<{ from: string; to: string; onTime: boolean; trains: number; avgDelay: number; onTimePct: number; onClick?: () => void }> = ({ from, to, onTime, trains, avgDelay, onTimePct, onClick }) => (
  <div onClick={onClick} className="bg-background border border-border p-5 rounded-xl cursor-pointer hover:border-primary/50 transition-all shadow-sm">
    <div className="flex justify-between items-center mb-3">
      <h4 className="font-bold text-text text-sm flex items-center gap-2">
        {from} <span className="text-textMuted">→</span> {to}
      </h4>
      <span className={`px-2.5 py-0.5 text-xs font-bold rounded-full border ${onTime ? 'bg-successBg text-success border-success/20' : 'bg-warningBg text-warning border-warning/20'}`}>
        {onTime ? 'On Time' : 'Delayed'}
      </span>
    </div>
    <div className="relative w-full h-1.5 bg-surface rounded-full mb-4 overflow-hidden">
      <div className={`h-full rounded-full ${onTime ? 'bg-success' : 'bg-warning'} w-3/4`}></div>
    </div>
    <div className="grid grid-cols-3 gap-2 text-center text-xs">
      <div>
        <div className="font-bold text-text">{trains}</div>
        <div className="text-[11px] text-textMuted">Active Trains</div>
      </div>
      <div>
        <div className={`font-bold ${avgDelay > 5 ? 'text-critical' : 'text-success'}`}>{avgDelay > 0 ? '+' : ''}{avgDelay} min</div>
        <div className="text-[11px] text-textMuted">Avg Delay</div>
      </div>
      <div>
        <div className="font-bold text-success">{onTimePct}%</div>
        <div className="text-[11px] text-textMuted">On Time</div>
      </div>
    </div>
  </div>
);

export const Dashboard: React.FC = () => {
  const { liveTrains } = useWebSocket();
  const [metrics, setMetrics] = React.useState({ accuracy: 94.2 });
  const [selectedRoute, setSelectedRoute] = React.useState<string | null>(null);
  
  React.useEffect(() => {
    const isLocalDev = window.location.hostname === 'localhost' && window.location.port === '5173';
    const apiBase = isLocalDev ? 'http://localhost:8000' : '';
    fetch(`${apiBase}/api/metrics`)
      .then(res => res.json())
      .then(data => setMetrics(data))
      .catch(err => console.error("Error fetching metrics", err));
  }, []);

  const activeCount = liveTrains.length;
  const onTimeCount = liveTrains.filter(t => t.status === 'ON_TIME').length;
  const delayedCount = liveTrains.filter(t => t.status === 'DELAYED').length;
  const criticalCount = liveTrains.filter(t => t.status === 'CRITICAL').length;
  
  const onTimePct = activeCount ? Math.round((onTimeCount / activeCount) * 100) : 0;
  const delayedPct = activeCount ? Math.round((delayedCount / activeCount) * 100) : 0;
  const criticalPct = activeCount ? Math.round((criticalCount / activeCount) * 100) : 0;

  const routeNames = ['Delhi -> Dehradun', 'Delhi -> Agra', 'Delhi -> Lucknow'];
  const routeStats = routeNames.map(route => {
    const trains = liveTrains.filter(t => t.route === route);
    const count = trains.length;
    const avgDelay = count ? (trains.reduce((sum, t) => sum + t.delayMin, 0) / count).toFixed(1) : "0.0";
    const onTimeRoute = trains.filter(t => t.status === 'ON_TIME').length;
    const onTimeRoutePct = count ? Math.round((onTimeRoute / count) * 100) : 0;
    return { route, count, avgDelay: parseFloat(avgDelay), onTimePct: onTimeRoutePct, onTime: onTimeRoutePct >= 50 };
  });

  const latestTrain = liveTrains[0];
  const simTime = latestTrain?.simTime || '06:45:00';

  return (
    <div className="space-y-6 pb-12">
      
      {/* 1. Compact Historical Context Toolbar */}
      <MonthContextSelector simTime={simTime} />

      {/* 2. Operational KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard title="Active Trains" value={activeCount} subValue="All Corridors" icon={Train} colorClass="text-primary" bgClass="bg-primary/10" />
        <StatCard title="On Time" value={onTimeCount} subValue={`${onTimePct}% Total`} icon={CheckCircle2} colorClass="text-success" bgClass="bg-successBg" />
        <StatCard title="Delayed" value={delayedCount} subValue={`${delayedPct}% Total`} icon={Clock} colorClass="text-warning" bgClass="bg-warningBg" />
        <StatCard title="Critical Delay" value={criticalCount} subValue={`${criticalPct}% Total`} icon={AlertTriangle} colorClass="text-critical" bgClass="bg-criticalBg" />
        <StatCard title="ETA Accuracy" value={`${metrics.accuracy.toFixed(1)}%`} subValue="Historical Test Set" icon={Activity} colorClass="text-primary" bgClass="bg-primary/10" />
      </div>

      {/* 3. Route Summaries */}
      <div>
        <h3 className="text-xs font-bold text-textMuted mb-3 uppercase tracking-wider">
          Corridor Performance Summary
        </h3>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {routeStats.map(stat => (
            <RouteProgress 
              key={stat.route}
              from={stat.route.split(' -> ')[0]} 
              to={stat.route.split(' -> ')[1]} 
              onTime={stat.onTime} 
              trains={stat.count} 
              avgDelay={stat.avgDelay} 
              onTimePct={stat.onTimePct} 
              onClick={() => setSelectedRoute(stat.route)}
            />
          ))}
        </div>
      </div>

      {/* 4. Live Trains Snapshot Table */}
      <div className="bg-background border border-border rounded-xl p-6 shadow-sm">
        <div className="flex justify-between items-center mb-5">
          <div>
            <h3 className="text-sm font-bold text-text uppercase tracking-wider">Live Trains Snapshot</h3>
            <p className="text-xs text-textMuted mt-0.5">Click any train or route to inspect detailed station timelines & trajectory graphs.</p>
          </div>
          <span className="text-xs text-primary font-semibold bg-primary/10 px-3 py-1 rounded-full border border-primary/20">
            {liveTrains.length} Live Telemetry Feeds
          </span>
        </div>

        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-left text-xs border-collapse whitespace-nowrap">
            <thead>
              <tr className="border-b border-border bg-surface text-textMuted uppercase font-semibold text-[11px]">
                <th className="py-3 px-4">Train ID & Name</th>
                <th className="py-3 px-4">Route</th>
                <th className="py-3 px-4">Current Station</th>
                <th className="py-3 px-4">Speed</th>
                <th className="py-3 px-4">Sched. ETA</th>
                <th className="py-3 px-4">AI Predicted ETA</th>
                <th className="py-3 px-4">Delay</th>
                <th className="py-3 px-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border bg-background">
              {liveTrains.map(train => (
                <tr 
                  key={train.id} 
                  onClick={() => setSelectedRoute(train.route)}
                  className="hover:bg-surface cursor-pointer transition-colors"
                >
                  <td className="py-3 px-4">
                    <div className="font-bold text-text">{train.id}</div>
                    <div className="text-[11px] text-textMuted">{train.name}</div>
                  </td>
                  <td className="py-3 px-4 text-text font-medium">{train.route}</td>
                  <td className="py-3 px-4 text-text">{train.currentLocation}</td>
                  <td className="py-3 px-4 font-bold text-primary">{train.currentSpeed?.toFixed(0) || 38} km/h</td>
                  <td className="py-3 px-4 text-text">{train.scheduledEta}</td>
                  <td className="py-3 px-4 font-bold text-primary">{train.aiEta}</td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold ${
                      train.delayMin > 15 ? 'bg-criticalBg text-critical border border-critical/20' :
                      train.delayMin > 0 ? 'bg-warningBg text-warning border border-warning/20' :
                      'bg-successBg text-success border border-success/20'
                    }`}>
                      {train.delayMin > 0 ? `+${train.delayMin}m` : 'On Time'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold border ${
                      train.status === 'ON_TIME'
                        ? 'bg-successBg text-success border-success/20'
                        : train.status === 'DELAYED'
                        ? 'bg-warningBg text-warning border-warning/20'
                        : 'bg-criticalBg text-critical border-critical/20'
                    }`}>
                      {train.status.replace('_', ' ')}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Route Detail Modal with Trajectory & Delay Charts */}
      {selectedRoute && (
        <RouteModal 
          routeName={selectedRoute} 
          trains={liveTrains.filter(t => t.route === selectedRoute)} 
          onClose={() => setSelectedRoute(null)} 
        />
      )}
    </div>
  );
};
