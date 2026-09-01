import React, { useState } from 'react';
import { Search, Filter, Eye } from 'lucide-react';
import { mockTrains } from '../data/mockData';
import { Link } from 'react-router-dom';

export const LiveTrains: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const filteredTrains = mockTrains.filter(train => {
    const matchesSearch = train.name.toLowerCase().includes(searchTerm.toLowerCase()) || train.id.includes(searchTerm);
    const matchesStatus = statusFilter === 'ALL' || train.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h2 className="text-2xl font-bold text-text">Live Trains</h2>
        
        <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
          <div className="relative">
            <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-textMuted" aria-hidden="true" />
            <input 
              type="text" 
              placeholder="Search train..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 bg-surface border border-border rounded-lg text-sm w-full sm:w-64 focus:outline-none focus:ring-2 focus:ring-primary text-text"
              aria-label="Search trains by name or number"
            />
          </div>
          <div className="relative">
            <Filter className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-textMuted" aria-hidden="true" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="pl-10 pr-8 py-2 bg-surface border border-border rounded-lg text-sm w-full sm:w-auto appearance-none focus:outline-none focus:ring-2 focus:ring-primary text-text"
              aria-label="Filter by train status"
            >
              <option value="ALL">All Status</option>
              <option value="ON_TIME">On Time</option>
              <option value="DELAYED">Delayed</option>
              <option value="CRITICAL">Critical</option>
            </select>
          </div>
        </div>
      </div>

      <div className="bg-background border border-border rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse" aria-label="Live Trains Detail Table">
            <thead>
              <tr className="bg-surface border-b border-border text-xs font-semibold text-textMuted uppercase">
                <th className="py-4 px-6">Train</th>
                <th className="py-4 px-6">Route</th>
                <th className="py-4 px-6">Current Location</th>
                <th className="py-4 px-6">Sched. ETA</th>
                <th className="py-4 px-6">AI ETA</th>
                <th className="py-4 px-6">Delay</th>
                <th className="py-4 px-6 text-center">Confidence</th>
                <th className="py-4 px-6">Status</th>
                <th className="py-4 px-6 text-center">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredTrains.map(train => (
                <tr key={train.id} className="border-b border-border last:border-0 hover:bg-surface/50 transition-colors">
                  <td className="py-4 px-6">
                    <div className="font-bold text-text">{train.id}</div>
                    <div className="text-sm text-textMuted">{train.name}</div>
                  </td>
                  <td className="py-4 px-6 text-sm text-text">{train.route}</td>
                  <td className="py-4 px-6">
                    <div className="text-sm font-medium text-text">{train.currentLocation}</div>
                    <div className="text-xs text-textMuted">{train.distanceRemaining} km to go</div>
                  </td>
                  <td className="py-4 px-6 text-sm text-text">{train.scheduledEta}</td>
                  <td className="py-4 px-6 text-sm font-bold text-text">{train.aiEta}</td>
                  <td className="py-4 px-6 text-sm font-bold">
                    <span className={train.delayMin > 5 ? 'text-critical' : train.delayMin > 0 ? 'text-warning' : 'text-success'}>
                      {train.delayMin > 0 ? '+' : ''}{train.delayMin} min
                    </span>
                  </td>
                  <td className="py-4 px-6 text-center">
                    <div className="inline-flex items-center justify-center w-10 h-10 rounded-full border-2 border-primary text-primary font-bold text-xs bg-primary/10">
                      {train.confidence}%
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border
                      ${train.status === 'ON_TIME' ? 'bg-successBg text-success border-success/20' : 
                        train.status === 'DELAYED' ? 'bg-warningBg text-warning border-warning/20' : 
                        'bg-criticalBg text-critical border-critical/20'}`}>
                      {train.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-center">
                    <Link to="/details" className="inline-flex p-2 text-textMuted hover:text-primary hover:bg-primary/10 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary" aria-label={`View details for train ${train.id}`}>
                      <Eye className="w-5 h-5" aria-hidden="true" />
                    </Link>
                  </td>
                </tr>
              ))}
              {filteredTrains.length === 0 && (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-textMuted">
                    No trains found matching the selected criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
