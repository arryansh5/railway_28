import React, { useState } from 'react';
import { Train, Clock, AlertTriangle, Activity, CheckCircle2, Info, X, ChevronDown, ChevronUp } from 'lucide-react';
import { useWebSocket, type Train as TrainType } from '../context/WebSocketContext';
import { MonthContextSelector } from '../components/MonthContextSelector';

const RouteModal: React.FC<{ routeName: string; trains: TrainType[]; onClose: () => void }> = ({ routeName, trains, onClose }) => {
  const [expandedWhy, setExpandedWhy] = useState<Record<string, boolean>>({});

  if (!routeName) return null;

  const toggleWhy = (trainId: string) => {
    setExpandedWhy(prev => ({ ...prev, [trainId]: !prev[trainId] }));
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-background border border-border rounded-xl w-full max-w-6xl shadow-2xl max-h-[90vh] flex flex-col overflow-hidden text-text">
        
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
              const isWhyOpen = !expandedWhy[train.id];
              const histCtx = train.historicalContext;
              const sys2 = train.system2Prediction;
              const sys3 = train.system3Decision;

              return (
                <div key={train.id} className="p-5 border border-border rounded-xl bg-surface shadow-sm space-y-4">
                  
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

                  {/* Expandable "Why? / Historical Context" Section */}
                  <div className="border border-border rounded-lg overflow-hidden bg-background">
                    <button
                      onClick={() => toggleWhy(train.id)}
                      className="w-full p-3 bg-surface hover:bg-border/50 flex items-center justify-between text-left text-xs font-bold text-text transition-colors"
                    >
                      <span className="flex items-center gap-2 text-primary">
                        <Info className="w-4 h-4" />
                        Why this ETA? View Historical Context & 4-Tier Prediction Breakdown
                      </span>
                      {isWhyOpen ? <ChevronUp className="w-4 h-4 text-textMuted" /> : <ChevronDown className="w-4 h-4 text-textMuted" />}
                    </button>

                    {isWhyOpen && (
                      <div className="p-4 border-t border-border space-y-3 text-xs">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                          
                          {/* Tier 1: Historical Context */}
                          <div className="p-3 bg-surface border border-border rounded-lg space-y-1">
                            <div className="font-bold text-primary uppercase text-[11px] flex items-center gap-1.5">
                              <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
                              1. Historical Prior
                            </div>
                            <div className="text-textMuted"><strong className="text-text">Month:</strong> {histCtx?.month || 'February'}</div>
                            <div className="text-textMuted"><strong className="text-text">Season:</strong> {histCtx?.season || 'Winter/Fog'}</div>
                            <div className="text-textMuted"><strong className="text-text">Fog Prior:</strong> {histCtx?.historical_fog_risk_pct ?? 100}%</div>
                            <div className="text-textMuted"><strong className="text-text">Congestion:</strong> {histCtx?.historical_congestion_risk_pct ?? 24}%</div>
                            <div className="text-[10px] text-textMuted mt-1">Sample N = {histCtx?.sample_count?.toLocaleString() || '1,915'}</div>
                          </div>

                          {/* Tier 2: System 2 Live Prediction */}
                          <div className="p-3 bg-surface border border-border rounded-lg space-y-1">
                            <div className="font-bold text-warning uppercase text-[11px] flex items-center gap-1.5">
                              <span className="w-1.5 h-1.5 rounded-full bg-warning"></span>
                              2. System 2 Prediction
                            </div>
                            <div className="text-textMuted"><strong className="text-text">Live Fog Risk:</strong> {sys2?.fogRiskPct ?? (train.delayMin > 10 ? 78 : 0)}%</div>
                            <div className="text-textMuted"><strong className="text-text">Congestion Risk:</strong> {sys2?.congestionRiskPct ?? 22}%</div>
                            <div className="text-textMuted"><strong className="text-text">Confidence:</strong> {train.confidence}%</div>
                            <div className="text-textMuted"><strong className="text-text">Speed Impact:</strong> {sys2?.expectedSpeedImpact || (train.delayMin > 10 ? 'MEDIUM' : 'NONE')}</div>
                            <div className="text-[10px] text-textMuted mt-1">Probabilistic Forecast</div>
                          </div>

                          {/* Tier 3: System 3 Dynamic Decision */}
                          <div className="p-3 bg-surface border border-border rounded-lg space-y-1">
                            <div className="font-bold text-critical uppercase text-[11px] flex items-center gap-1.5">
                              <span className="w-1.5 h-1.5 rounded-full bg-critical"></span>
                              3. System 3 Decision
                            </div>
                            <div className="text-textMuted"><strong className="text-text">Restriction:</strong> {sys3?.actionType || (train.delayMin > 10 ? 'ACTIVE' : 'INACTIVE')}</div>
                            <div className="text-textMuted"><strong className="text-text">Speed Cap:</strong> {sys3?.speedCapKmph ? `${sys3.speedCapKmph} km/h` : 'Line Speed'}</div>
                            <div className="text-textMuted truncate"><strong className="text-text">Decision:</strong> {sys3?.reason || train.delayReason || 'Clear'}</div>
                            <div className="text-[10px] text-textMuted mt-1">Dynamic Restriction Lifecycle</div>
                          </div>

                          {/* Tier 4: System 1 Physics & Dynamic ETA */}
                          <div className="p-3 bg-surface border border-border rounded-lg space-y-1">
                            <div className="font-bold text-success uppercase text-[11px] flex items-center gap-1.5">
                              <span className="w-1.5 h-1.5 rounded-full bg-success"></span>
                              4. System 1 Physics & ETA
                            </div>
                            <div className="text-textMuted"><strong className="text-text">Velocity:</strong> {train.currentSpeed?.toFixed(0) || 38} km/h</div>
                            <div className="text-textMuted"><strong className="text-text">Sched Arrival:</strong> {train.scheduledEta}</div>
                            <div className="text-textMuted"><strong className="text-text">Dynamic AI ETA:</strong> {train.aiEta}</div>
                            <div className="text-textMuted"><strong className="text-text">Delay:</strong> +{train.delayMin} min</div>
                            <div className="text-[10px] text-success font-semibold mt-1">Closed-Loop Synchronized</div>
                          </div>

                        </div>

                        <div className="p-2.5 bg-surface/80 rounded border border-border text-[11px] text-textMuted leading-relaxed">
                          <strong className="text-text">Explanation:</strong> Month selection provides historical environmental priors (Tier 1). System 2 evaluates kinematics + priors to forecast live risks (Tier 2). System 3 creates dynamic speed caps when thresholds are met (Tier 3). System 1 physics executes physical deceleration and ML updates dynamic ETA (Tier 4). At 09:00 AM, fog clears and train accelerates back to 110 km/h.
                        </div>
                      </div>
                    )}
                  </div>

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
                              <th className="py-2.5 px-3">Factor</th>
                              <th className="py-2.5 px-3 text-right">Destination ETA</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border bg-background">
                            {(train.timeline || []).map((st: any, i: number) => {
                              const isTerminal = i === (train.timeline?.length || 0) - 1;
                              const stationConfidence = Math.max(45, train.confidence - (i * 2));
                              
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
                                  <td className="py-2.5 px-3 text-[11px] text-textMuted max-w-[150px] truncate" title={train.delayReason || 'Clear'}>
                                    {st.delay > 0 ? (
                                      <span className="flex items-center gap-1 text-critical">
                                        <AlertTriangle className="w-3 h-3 shrink-0" /> {train.delayReason || 'Network Delay'}
                                      </span>
                                    ) : (
                                      <span className="text-textMuted">Normal Cruising</span>
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
            <p className="text-xs text-textMuted mt-0.5">Click any train or route to inspect detailed station timelines & 4-tier diagnostics.</p>
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

      {/* Route Detail Modal with 4-Tier Diagnostics */}
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
