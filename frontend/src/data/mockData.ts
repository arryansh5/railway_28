
export const mockEtaTrend = [
  { time: '08:00', scheduled: 12.16, ai: 12.16, actual: null }, // Using decimal hours for simplicity in charts if needed, or strings
  { time: '09:00', scheduled: 12.16, ai: 12.25, actual: null },
  { time: '10:00', scheduled: 12.16, ai: 12.35, actual: null },
  { time: '11:00', scheduled: 12.16, ai: 12.43, actual: null },
  { time: '12:00', scheduled: 12.16, ai: 12.50, actual: null },
];

export const mockFactors = [
  { name: 'Weather/Fog', impact: 40, positive: false },
  { name: 'Track Congestion', impact: 35, positive: false },
  { name: 'Previous Delay', impact: 20, positive: false },
  { name: 'Speed Recovery', impact: 15, positive: true },
];

export const mockAlerts = [
  {
    id: 1,
    title: 'Train 12430 (Lucknow Express)',
    description: 'Predicted delay > 15 minutes',
    time: '10:28',
    level: 'CRITICAL'
  },
  {
    id: 2,
    title: 'Platform 8 may have conflict',
    description: 'Between Train 12280 & 12618',
    time: '10:24',
    level: 'WARNING'
  },
  {
    id: 3,
    title: 'Low confidence prediction',
    description: 'Train 12259 (Confidence: 62%)',
    time: '10:21',
    level: 'INFO'
  }
];
