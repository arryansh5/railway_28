import React, { useState } from 'react';
import { ArrowRight, Train, ArrowUpDown } from 'lucide-react';

export const TrainSearch: React.FC = () => {
  const [fromStation, setFromStation] = useState('');
  const [toStation, setToStation] = useState('');

  const handleSwap = () => {
    const temp = fromStation;
    setFromStation(toStation);
    setToStation(temp);
  };
  return (
    <div className="space-y-4 font-sans w-full">
      {/* Find Trains Card */}
      <div className="bg-background border border-border rounded-xl overflow-hidden shadow-sm">
        {/* Header */}
        <div className="px-5 py-4 flex items-center gap-3 border-b border-border bg-surface/50">
          <div className="bg-primary/10 p-2 rounded-lg flex items-center justify-center border border-primary/20">
            <ArrowRight className="w-4 h-4 text-primary" />
          </div>
          <h2 className="text-text font-bold text-sm uppercase tracking-wider">Find Trains</h2>
        </div>

        {/* Body */}
        <div className="p-6 relative">
          <div className="flex flex-col gap-5 relative pr-14">
            {/* Connecting Line */}
            <div className="absolute left-[11px] top-[24px] bottom-[24px] w-[2px] bg-border z-0"></div>

            {/* From Station */}
            <div className="flex items-center gap-4 relative z-10">
              <div className="w-[24px] h-[24px] rounded-full border-[3px] border-success bg-background flex-shrink-0"></div>
              <input 
                type="text" 
                placeholder="From Station" 
                value={fromStation}
                onChange={(e) => setFromStation(e.target.value)}
                className="w-full bg-transparent text-text placeholder-textMuted font-medium text-sm focus:outline-none py-1"
              />
            </div>
            
            {/* Divider */}
            <div className="h-[1px] w-full bg-border absolute top-1/2 left-0 -translate-y-1/2 z-0"></div>

            {/* To Station */}
            <div className="flex items-center gap-4 relative z-10">
              <div className="w-[24px] h-[24px] rounded-full border-[3px] border-primary bg-background flex-shrink-0"></div>
              <input 
                type="text" 
                placeholder="To Station" 
                value={toStation}
                onChange={(e) => setToStation(e.target.value)}
                className="w-full bg-transparent text-text placeholder-textMuted font-medium text-sm focus:outline-none py-1"
              />
            </div>
            
            {/* Swap Button */}
            <button 
              onClick={handleSwap}
              className="absolute right-0 top-1/2 -translate-y-1/2 p-2.5 bg-surface hover:bg-border/50 text-textMuted hover:text-text rounded-full border border-border transition-colors z-10 shadow-sm"
              title="Swap stations"
            >
              <ArrowUpDown className="w-4 h-4" />
            </button>
          </div>

          <button className="w-full mt-8 bg-primary hover:bg-primaryHover text-white font-bold py-3.5 rounded-lg flex items-center justify-center gap-2 transition-colors shadow-sm">
            View Trains <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Live Train Status Card */}
      <div className="bg-background border border-border rounded-xl overflow-hidden shadow-sm">
        {/* Header */}
        <div className="px-5 py-4 flex items-center gap-3 border-b border-border bg-surface/50">
          <div className="bg-primary/10 p-2 rounded-lg flex items-center justify-center border border-primary/20">
            <Train className="w-4 h-4 text-primary" />
          </div>
          <h2 className="text-text font-bold text-sm uppercase tracking-wider">Live Train Status</h2>
        </div>

        {/* Body */}
        <div className="p-6">
          <div className="relative">
            <input 
              type="text" 
              placeholder="Enter train number or name..." 
              className="w-full bg-surface border border-border rounded-lg pl-4 pr-12 py-3.5 text-sm text-text placeholder-textMuted font-medium focus:outline-none focus:border-primary/50 transition-colors shadow-inner"
            />
            <button className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-primary hover:bg-primaryHover text-white rounded-md transition-colors shadow-sm">
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
