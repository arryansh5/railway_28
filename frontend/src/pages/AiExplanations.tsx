import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell } from 'recharts';
import { BrainCircuit, Info } from 'lucide-react';
import { mockFactors } from '../data/mockData';

export const AiExplanations: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-text">AI Prediction Explanation</h2>
          <p className="text-textMuted mt-1">Understanding the factors influencing Train 12430's ETA</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Factors Breakdown */}
        <div className="lg:col-span-2 bg-background border border-border rounded-xl p-6">
          <div className="flex items-center gap-2 mb-6">
            <BrainCircuit className="w-6 h-6 text-primary" aria-hidden="true" />
            <h3 className="text-lg font-bold text-text uppercase tracking-wider">Factor Contributions</h3>
          </div>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={mockFactors} margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={true} vertical={false} />
                <XAxis type="number" stroke="#64748b" tick={{ fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis dataKey="name" type="category" stroke="#0f172a" tick={{ fill: '#0f172a', fontWeight: 500 }} axisLine={false} tickLine={false} width={120} />
                <RechartsTooltip 
                  cursor={{fill: '#f8fafc'}}
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px' }}
                  formatter={(value: any) => [`${value}% impact`, 'Contribution']}
                />
                <Bar dataKey="impact" radius={[0, 4, 4, 0]} barSize={32}>
                  {
                    mockFactors.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.positive ? '#16a34a' : '#dc2626'} />
                    ))
                  }
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 flex gap-6 text-sm justify-center border-t border-border pt-4">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-critical"></span>
              <span className="text-textMuted">Increases Delay (Negative)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-success"></span>
              <span className="text-textMuted">Reduces Delay (Positive)</span>
            </div>
          </div>
        </div>

        {/* Textual Explanation */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-surface border border-border rounded-xl p-6">
            <h3 className="text-lg font-bold text-text mb-4">Summary</h3>
            <p className="text-text leading-relaxed">
              The AI model predicts a <strong>16-minute delay</strong> for Train 12430 upon arriving at Lucknow.
            </p>
            <p className="text-text leading-relaxed mt-4">
              The most significant factor is <strong>Weather/Fog (40% impact)</strong> on the current route segment, which typically reduces average speed by 15-20 km/h in this region.
            </p>
            <p className="text-text leading-relaxed mt-4">
              There is a slight positive effect from <strong>Speed Recovery (15%)</strong>, as the train has historically made up time on the straight section past Kanpur.
            </p>
          </div>

          <div className="bg-primary/10 border border-primary/20 rounded-xl p-6 flex items-start gap-4">
            <Info className="w-6 h-6 text-primary shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <h4 className="font-bold text-primary mb-1">High Confidence</h4>
              <p className="text-sm text-textMuted">The prediction confidence is 85%. Data from 4 weather stations and 12 previous trains on this route today have corroborated the conditions.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
