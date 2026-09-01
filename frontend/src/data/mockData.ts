export type TrainStatus = 'ON_TIME' | 'DELAYED' | 'CRITICAL';

export interface Train {
  id: string;
  name: string;
  route: string;
  currentLocation: string;
  distanceRemaining: number;
  scheduledEta: string;
  aiEta: string;
  delayMin: number;
  confidence: number;
  status: TrainStatus;
}

export const mockTrains: Train[] = [
  {
    id: '12055',
    name: 'Shatabdi Express',
    route: 'Delhi -> Dehradun',
    currentLocation: 'Meerut Cantt',
    distanceRemaining: 120,
    scheduledEta: '10:45',
    aiEta: '10:50',
    delayMin: 5,
    confidence: 93,
    status: 'DELAYED',
  },
  {
    id: '12280',
    name: 'Jan Shatabdi',
    route: 'Delhi -> Agra',
    currentLocation: 'Mathura Jn',
    distanceRemaining: 55,
    scheduledEta: '11:15',
    aiEta: '11:25',
    delayMin: 10,
    confidence: 89,
    status: 'DELAYED',
  },
  {
    id: '12430',
    name: 'Lucknow Express',
    route: 'Delhi -> Lucknow',
    currentLocation: 'Kanpur Central',
    distanceRemaining: 110,
    scheduledEta: '12:10',
    aiEta: '12:26',
    delayMin: 16,
    confidence: 85,
    status: 'CRITICAL',
  },
  {
    id: '12009',
    name: 'Dehradun Express',
    route: 'Delhi -> Dehradun',
    currentLocation: 'Muzaffarnagar',
    distanceRemaining: 80,
    scheduledEta: '11:05',
    aiEta: '11:03',
    delayMin: -2,
    confidence: 95,
    status: 'ON_TIME',
  },
  {
    id: '12618',
    name: 'Tamil Nadu Express',
    route: 'Delhi -> Lucknow',
    currentLocation: 'Etawah',
    distanceRemaining: 160,
    scheduledEta: '12:35',
    aiEta: '12:37',
    delayMin: 2,
    confidence: 91,
    status: 'ON_TIME',
  },
];

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
