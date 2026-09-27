export interface Station {
  code: string;
  name: string;
  arrival: string;
  departure: string;
  distance: number;
  platform: string;
  isPassed: boolean;
  coordinates: [number, number]; // [longitude, latitude]
}

export interface TrainInfo {
  id: string;
  name: string;
  number: string;
  currentStationIndex: number;
  delayMinutes: number;
  status: 'Running' | 'Arrived' | 'Not Started';
  route: Station[];
  currentLocation: [number, number];
  heading: number; // degrees for rotation
}

// Generate a realistic route across India (roughly Delhi to Mumbai)
export const mockTrainData: TrainInfo = {
  id: 'train-12954',
  name: 'Hazrat Nizamuddin - Mumbai Central Tejas Rajdhani',
  number: '12954',
  currentStationIndex: 2,
  delayMinutes: 7,
  status: 'Running',
  currentLocation: [75.83, 25.18], // Near Kota
  heading: 210, // Southwest
  route: [
    {
      code: 'NZM',
      name: 'Hazrat Nizamuddin',
      arrival: '17:15',
      departure: '17:15',
      distance: 0,
      platform: 'PF 4',
      isPassed: true,
      coordinates: [77.25, 28.58],
    },
    {
      code: 'MTJ',
      name: 'Mathura Jn',
      arrival: '18:43',
      departure: '18:45',
      distance: 134,
      platform: 'PF 2',
      isPassed: true,
      coordinates: [77.67, 27.49],
    },
    {
      code: 'KOTA',
      name: 'Kota Jn',
      arrival: '21:30',
      departure: '21:40',
      distance: 458,
      platform: 'PF 2',
      isPassed: false,
      coordinates: [75.83, 25.18],
    },
    {
      code: 'RTM',
      name: 'Ratlam Jn',
      arrival: '01:05',
      departure: '01:07',
      distance: 725,
      platform: 'PF 4',
      isPassed: false,
      coordinates: [75.03, 23.33],
    },
    {
      code: 'BRC',
      name: 'Vadodara Jn',
      arrival: '04:29',
      departure: '04:39',
      distance: 985,
      platform: 'PF 1',
      isPassed: false,
      coordinates: [73.18, 22.30],
    },
    {
      code: 'MMCT',
      name: 'Mumbai Central',
      arrival: '08:35',
      departure: '08:35',
      distance: 1383,
      platform: 'PF 1',
      isPassed: false,
      coordinates: [72.82, 18.97],
    },
  ],
};

// Generate some other mock trains across the map for visual effect
export const mockOtherTrains = [
  { id: '1', name: '02563 NDLS Clone', coords: [79.93, 23.18], heading: 120 },
  { id: '2', name: '12301 Howrah Rajdhani', coords: [82.13, 25.18], heading: 290 },
  { id: '3', name: '12628 Karnataka Exp', coords: [77.59, 12.97], heading: 350 },
  { id: '4', name: '12834 Howrah Exp', coords: [86.98, 22.80], heading: 180 },
  { id: '5', name: '12431 Rajdhani Exp', coords: [73.2, 19.1], heading: 20 },
];
