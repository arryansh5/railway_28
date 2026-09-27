const fs = require('fs');
const path = require('path');

const stations = [
  { id: 'NDLS', name: 'New Delhi', coords: [77.2197, 28.6433] },
  { id: 'SRE', name: 'Saharanpur', coords: [77.5540, 29.9640] },
  { id: 'UMB', name: 'Ambala Cantt', coords: [76.8286, 30.3340] },
  { id: 'CDG', name: 'Chandigarh', coords: [76.8000, 30.7046] },
  { id: 'LDH', name: 'Ludhiana', coords: [75.8573, 30.9010] },
  { id: 'JUC', name: 'Jalandhar City', coords: [75.5792, 31.3256] },
  { id: 'ASR', name: 'Amritsar', coords: [74.8723, 31.6340] },
  { id: 'PTK', name: 'Pathankot', coords: [75.6469, 32.2689] },
  { id: 'JAT', name: 'Jammu Tawi', coords: [74.8756, 32.7099] },
  { id: 'SVDK', name: 'Katra (SVDK)', coords: [74.9312, 32.9904] },
  { id: 'BTI', name: 'Bathinda', coords: [74.9398, 30.2104] },
  { id: 'FZR', name: 'Firozpur', coords: [74.6069, 30.9295] },
  { id: 'MB', name: 'Moradabad', coords: [78.7766, 28.8351] },
  { id: 'LKO', name: 'Lucknow', coords: [80.9230, 26.8300] },
  { id: 'BE', name: 'Bareilly', coords: [79.4182, 28.3512] },
];

const paths = [
  // Delhi to SVDK (Main Northern Line)
  ['NDLS', 'UMB', 'LDH', 'JUC', 'PTK', 'JAT', 'SVDK'],
  // Ambala to Chandigarh
  ['UMB', 'CDG'],
  // Jalandhar to Amritsar
  ['JUC', 'ASR'],
  // Delhi to Bathinda
  ['NDLS', 'BTI', 'FZR'],
  // Delhi to Lucknow via Moradabad/Bareilly
  ['NDLS', 'MB', 'BE', 'LKO'],
  // Ambala to Saharanpur to Moradabad
  ['UMB', 'SRE', 'MB']
];

const features = [];

// Create station features
stations.forEach(s => {
  features.push({
    type: 'Feature',
    geometry: { type: 'Point', coordinates: s.coords },
    properties: { type: 'station', name: s.name, id: s.id }
  });
});

// Create track features
paths.forEach(route => {
  const coordinates = route.map(stationId => {
    return stations.find(s => s.id === stationId).coords;
  });
  
  features.push({
    type: 'Feature',
    geometry: { type: 'LineString', coordinates },
    properties: { type: 'track' }
  });
});

const geojson = {
  type: 'FeatureCollection',
  features
};

const outputPath = path.join(__dirname, '../public/northern_railway.geojson');
fs.writeFileSync(outputPath, JSON.stringify(geojson, null, 2));

console.log(`Successfully generated mock Northern Railway GeoJSON at ${outputPath}`);
