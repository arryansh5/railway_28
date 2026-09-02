import React from 'react';
import { Train, Clock, AlertTriangle, Activity, CheckCircle2, Info, X } from 'lucide-react';
import { ComposedChart, BarChart, Bar, LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend } from 'recharts';
import { useWebSocket } from '../context/WebSocketContext';

// Helper for modal
const parseTime = (timeStr: string) => {
  if (!timeStr) return 0;
  const [h, m] = timeStr.split(':').map(Number);
  return h * 60 + m;
};

const formatTime = (minutes: number) => {
  const h = Math.floor(minutes / 60);
  const m = Math.floor(minutes % 60);
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
};

const RouteModal: React.FC<{ routeName: string, trains: any[], onClose: () => void }> = ({ routeName, trains, onClose }) => {
  if (!routeName) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-background border border-border rounded-xl w-full max-w-6xl shadow-2xl max-h-[90vh] flex flex-col">
        <div className="p-6 border-b border-border flex justify-between items-center bg-surface rounded-t-xl">
          <h2 className="text-xl font-bold text-text flex items-center gap-2">
            <Train className="w-6 h-6 text-primary" />
            Route Details: {routeName}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-border rounded-lg transition-colors">
            <X className="w-5 h-5 text-textMuted" />
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto flex-1">
          {trains.length === 0 ? (
            <div className="text-center text-textMuted py-8">No active trains on this route right now.</div>
          ) : (
            <div className="space-y-4">
              {trains.map(train => (
                <div key={train.id} className="p-5 border border-border rounded-lg bg-surface hover:border-primary/30 transition-colors">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="font-bold text-lg text-text">{train.id} - {train.name}</h3>
                      <p className="text-sm text-textMuted flex items-center gap-1 mt-1">
                        <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
                        Currently at: <span className="font-medium text-text">{train.currentLocation}</span> ({train.distanceRemaining.toFixed(1)} km to go)
                      </p>
                    </div>
                    <span className={`px-3 py-1 text-xs font-bold rounded-full border ${train.status === 'ON_TIME' ? 'bg-successBg text-success border-success/20' : train.status === 'DELAYED' ? 'bg-warningBg text-warning border-warning/20' : 'bg-criticalBg text-critical border-critical/20'}`}>
                      {train.status.replace('_', ' ')}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-background p-4 rounded-lg border border-border">
                    <div>
                      <div className="text-xs text-textMuted uppercase">Scheduled ETA</div>
                      <div className="font-semibold text-text">{train.scheduledEta}</div>
                    </div>
                    <div>
                      <div className="text-xs text-textMuted uppercase">AI Predicted ETA</div>
                      <div className="font-bold text-primary">{train.aiEta}</div>
                    </div>
                    <div>
                      <div className="text-xs text-textMuted uppercase">Delay</div>
                      <div className={`font-semibold ${train.delayMin > 0 ? 'text-critical' : 'text-success'}`}>{train.delayMin > 0 ? `+${train.delayMin}` : train.delayMin} min</div>
                    </div>
                    <div>
                      <div className="text-xs text-textMuted uppercase">AI Confidence</div>
                      <div className="font-semibold text-text">{train.confidence}%</div>
                    </div>
                  </div>
                  
                  {train.delayMin > 0 && train.delayReason && (
                    <div className="mt-4 p-3 bg-criticalBg border border-critical/20 rounded-lg flex items-start gap-2">
                      <AlertTriangle className="w-5 h-5 text-critical shrink-0 mt-0.5" />
                      <div>
                        <div className="text-sm font-bold text-critical">Delay Factor Identified</div>
                        <div className="text-sm text-critical/80">{train.delayReason}</div>
                      </div>
                    </div>
                  )}

                  {train.timeline && train.timeline.length > 0 && (
                    <div className="mt-6 border-t border-border pt-4">
                      <h4 className="text-sm font-bold text-text mb-4 uppercase tracking-wider flex items-center gap-2">
                        <Activity className="w-4 h-4 text-primary" />
                        Station-wise Prediction Analysis
                      </h4>

                      <div className="overflow-x-auto mb-6">
                        <table className="w-full text-left text-sm border-collapse whitespace-nowrap">
                          <thead>
                            <tr className="border-b border-border text-xs font-semibold text-textMuted uppercase">
                              <th className="pb-3 pr-4">Station</th>
                              <th className="pb-3 px-4">Scheduled</th>
                              <th className="pb-3 px-4">Predicted</th>
                              <th className="pb-3 px-4">Delay</th>
                              <th className="pb-3 px-4">Confidence</th>
                              <th className="pb-3 px-4">Reason</th>
                              <th className="pb-3 px-4">Next St. ETA</th>
                              <th className="pb-3 pl-4 text-right">Terminal ETA</th>
                            </tr>
                          </thead>
                          <tbody>
                            {train.timeline.map((st: any, i: number) => {
                              const isTerminal = i === train.timeline.length - 1;
                              const nextSt = train.timeline[i+1];
                              const stationConfidence = Math.max(45, train.confidence - (i * 2));
                              
                              return (
                                <tr key={i} className="border-b border-border last:border-0 hover:bg-surface transition-colors">
                                  <td className="py-3 pr-4">
                                    <div className="font-bold text-text flex items-center gap-2">
                                      {st.stationName}
                                      {isTerminal && <span className="text-[10px] font-bold px-1.5 py-0.5 bg-primary/10 text-primary rounded">TERM</span>}
                                    </div>
                                    <div className="text-xs text-textMuted">{st.stationCode}</div>
                                  </td>
                                  <td className="py-3 px-4 text-text">{st.scheduled}</td>
                                  <td className="py-3 px-4 font-semibold text-primary">{st.predicted}</td>
                                  <td className="py-3 px-4">
                                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${st.delay > 15 ? 'bg-criticalBg text-critical' : st.delay > 0 ? 'bg-warningBg text-warning' : 'bg-successBg text-success'}`}>
                                      {st.delay > 0 ? `+${st.delay}m` : 'On Time'}
                                    </span>
                                  </td>
                                  <td className="py-3 px-4 font-medium text-text flex items-center gap-1">
                                    <CheckCircle2 className="w-3 h-3 text-success" /> {stationConfidence}%
                                  </td>
                                  <td className="py-3 px-4 text-xs font-medium text-critical max-w-[150px] truncate" title={train.delayReason || 'Network Delay'}>
                                    {st.delay > 0 ? (
                                      <span className="flex items-center gap-1">
                                        <AlertTriangle className="w-3 h-3" /> {train.delayReason || 'Network Delay'}
                                      </span>
                                    ) : '-'}
                                  </td>
                                  <td className="py-3 px-4 font-medium text-text">{!isTerminal && nextSt ? nextSt.predicted : '-'}</td>
                                  <td className="py-3 pl-4 text-right font-bold text-text">{train.aiEta}</td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>

                      <div className="grid grid-cols-1 gap-6 mb-4">
                        {/* Graph 1: ETA Trend */}
                        <div className="h-72 w-full border border-border rounded-xl bg-surface p-5 pb-2 flex flex-col">
                          <h5 className="font-bold text-text mb-4 text-sm uppercase tracking-wider">ETA Trend</h5>
                          <div className="flex-1 min-h-0">
                            <ResponsiveContainer width="100%" height="100%">
                              <LineChart data={train.timeline.map((st: any) => ({
                                name: st.stationCode,
                                predictedMin: parseTime(st.predicted),
                                scheduledMin: parseTime(st.scheduled),
                                predicted: st.predicted,
                                scheduled: st.scheduled
                              }))} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.3} />
                                <XAxis dataKey="name" tick={{fontSize: 10, fill: '#64748b'}} axisLine={false} tickLine={false} dy={10} />
                                <YAxis 
                                  domain={['auto', 'auto']} 
                                  tickFormatter={formatTime} 
                                  tick={{fontSize: 10, fill: '#64748b'}} 
                                  axisLine={false} 
                                  tickLine={false} 
                                />
                                <RechartsTooltip 
                                  contentStyle={{backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f8fafc', fontSize: '12px'}}
                                  labelStyle={{color: '#94a3b8', marginBottom: '4px'}}
                                  formatter={(value: any, name: string, props: any) => {
                                    if (name === 'AI Predicted ETA') return [props.payload.predicted, name];
                                    if (name === 'Scheduled ETA') return [props.payload.scheduled, name];
                                    return [value, name];
                                  }}
                                />
                                <Legend wrapperStyle={{fontSize: '12px', color: '#64748b', paddingTop: '10px'}} />
                                <Line type="monotone" dataKey="predictedMin" stroke="#3b82f6" strokeWidth={2} dot={{r: 4, fill: '#3b82f6', strokeWidth: 0}} activeDot={{r: 6}} name="AI Predicted ETA" />
                                <Line type="monotone" dataKey="scheduledMin" stroke="#94a3b8" strokeWidth={2} strokeDasharray="5 5" dot={{r: 3, fill: '#94a3b8', strokeWidth: 0}} name="Scheduled ETA" />
                              </LineChart>
                            </ResponsiveContainer>
                          </div>
                        </div>

                        {/* Graph 2: Delay Analysis */}
                        <div className="h-64 w-full border border-border rounded-xl bg-surface p-5 pb-2 flex flex-col">
                          <h5 className="font-bold text-text mb-4 uppercase text-sm tracking-wider">Station Delays (Mins)</h5>
                          <div className="flex-1 min-h-0">
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart data={train.timeline.map((st: any) => ({
                                name: st.stationCode,
                                delay: st.delay
                              }))} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.3} />
                                <XAxis dataKey="name" tick={{fontSize: 10, fill: '#64748b'}} axisLine={false} tickLine={false} dy={10} />
                                <YAxis tick={{fontSize: 10, fill: '#64748b'}} axisLine={false} tickLine={false} />
                                <RechartsTooltip 
                                  contentStyle={{backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f8fafc', fontSize: '12px'}}
                                  cursor={{fill: 'rgba(255,255,255,0.05)'}}
                                />
                                <Bar dataKey="delay" fill="#ef4444" radius={[4, 4, 0, 0]} name="Delay (mins)" maxBarSize={40} />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>

                        {/* Graph 3: AI Confidence */}
                        {/* <div className="h-56 w-full border border-border rounded-xl bg-surface p-5 pb-2 flex flex-col">
                          <h5 className="font-bold text-text mb-4 uppercase text-sm tracking-wider">AI Confidence Trend</h5>
                          <div className="flex-1 min-h-0">
                            <ResponsiveContainer width="100%" height="100%">
                              <AreaChart data={train.timeline.map((st: any, i: number) => ({
                                name: st.stationCode,
                                confidence: Math.max(45, train.confidence - (i * 2))
                              }))} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                                <defs>
                                  <linearGradient id={`colorConf-${train.id}`} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                                  </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.3} />
                                <XAxis dataKey="name" tick={{fontSize: 10, fill: '#64748b'}} axisLine={false} tickLine={false} dy={10} />
                                <YAxis domain={[0, 100]} tick={{fontSize: 10, fill: '#64748b'}} axisLine={false} tickLine={false} />
                                <RechartsTooltip 
                                  contentStyle={{backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f8fafc', fontSize: '12px'}}
                                />
                                <Area type="monotone" dataKey="confidence" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill={`url(#colorConf-${train.id})`} name="Confidence %" />
                              </AreaChart>
                            </ResponsiveContainer>
                          </div>
                        </div> */}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

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

const RouteProgress: React.FC<{ from: string, to: string, onTime: boolean, trains: number, avgDelay: number, onTimePct: number, onClick?: () => void }> = ({ from, to, onTime, trains, avgDelay, onTimePct, onClick }) => (
  <div onClick={onClick} className="bg-background border border-border p-5 rounded-xl cursor-pointer hover:border-primary/50 transition-colors">
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
  const { liveTrains } = useWebSocket();
  const [metrics, setMetrics] = React.useState({ accuracy: 91.2 });
  const [selectedRoute, setSelectedRoute] = React.useState<string | null>(null);
  
  React.useEffect(() => {
    fetch('http://localhost:8000/api/metrics')
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

  // Calculate dynamic route summaries
  const routeNames = ['Delhi -> Dehradun', 'Delhi -> Agra', 'Delhi -> Lucknow'];
  const routeStats = routeNames.map(route => {
    const trains = liveTrains.filter(t => t.route === route);
    const count = trains.length;
    const avgDelay = count ? (trains.reduce((sum, t) => sum + t.delayMin, 0) / count).toFixed(1) : "0.0";
    const onTimeRoute = trains.filter(t => t.status === 'ON_TIME').length;
    const onTimePct = count ? Math.round((onTimeRoute / count) * 100) : 0;
    return { route, count, avgDelay: parseFloat(avgDelay), onTimePct, onTime: onTimePct >= 50 };
  });

  // Generate dynamic alerts
  const dynamicAlerts = liveTrains
    .filter(t => t.status === 'CRITICAL' || t.status === 'DELAYED')
    .map(t => ({
      id: `alert-${t.id}`,
      level: t.status === 'CRITICAL' ? 'CRITICAL' : 'WARNING',
      title: `Train ${t.id} (${t.name})`,
      description: `Predicted delay > ${t.delayMin} minutes. AI ETA is ${t.aiEta}.`,
      time: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
    }));

  // Append a default alert if we have few so the box isn't empty
  if (dynamicAlerts.length < 2) {
    dynamicAlerts.push({
      id: 'alert-system-1',
      level: 'INFO',
      title: 'Low confidence prediction',
      description: 'Train 12259 (Confidence: 62%) due to weather sensor loss.',
      time: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
    });
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-text">Overview</h2>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-6">
        <StatCard title="Active Trains" value={activeCount} subValue="All Routes" icon={Train} colorClass="text-primary" bgClass="bg-primary/10" />
        <StatCard title="On Time" value={onTimeCount} subValue={`${onTimePct}%`} icon={CheckCircle2} colorClass="text-success" bgClass="bg-successBg" />
        <StatCard title="Delayed" value={delayedCount} subValue={`${delayedPct}%`} icon={Clock} colorClass="text-warning" bgClass="bg-warningBg" />
        <StatCard title="Critical Delay" value={criticalCount} subValue={`${criticalPct}%`} icon={AlertTriangle} colorClass="text-critical" bgClass="bg-criticalBg" />
        <StatCard title="ETA Accuracy" value={`${metrics.accuracy.toFixed(1)}%`} subValue="" icon={Activity} colorClass="text-primary" bgClass="bg-primary/10" />
      </div>

      {/* Route Summaries */}
      <div>
        <h3 className="text-lg font-bold text-text mb-4 uppercase tracking-wider">Route Summary</h3>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
                {liveTrains.slice(0, 4).map(train => (
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
            {dynamicAlerts.slice(0, 5).map(alert => (
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
