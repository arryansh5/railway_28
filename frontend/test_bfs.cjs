const fs = require('fs');
const path = 'public/northern_railway_real.geojson';
const data = JSON.parse(fs.readFileSync(path));

const stations = [];
const tracks = [];
data.features.forEach((f, index) => {
  if (f.properties.type === 'station') {
    if (!f.properties.stationId) f.properties.stationId = `station_${index}`;
    stations.push(f);
  } else if (f.properties.type === 'track') {
    tracks.push(f);
  }
});

const graph = {};
function roundCoord(coord) { return `${coord[0].toFixed(3)},${coord[1].toFixed(3)}`; }
tracks.forEach(track => {
  let coordsList = track.geometry.type === 'LineString' ? [track.geometry.coordinates] : track.geometry.coordinates;
  coordsList.forEach(coords => {
    if (!coords || coords.length < 2) return;
    for (let i = 0; i < coords.length - 1; i++) {
      const u = roundCoord(coords[i]);
      const v = roundCoord(coords[i + 1]);
      if (u !== v) {
        if (!graph[u]) graph[u] = new Set();
        if (!graph[v]) graph[v] = new Set();
        graph[u].add(v);
        graph[v].add(u);
      }
    }
  });
});

const nodeToStations = {};
function distance(lng1, lat1, lng2, lat2) { return Math.sqrt((lng1-lng2)**2 + (lat1-lat2)**2); }

// Mark all nodes within 0.01 deg (~1km) of a station as belonging to it
stations.forEach(station => {
  const p = station.geometry.coordinates;
  for (const nodeStr of Object.keys(graph)) {
    const [lngStr, latStr] = nodeStr.split(',');
    const d = distance(p[0], p[1], parseFloat(lngStr), parseFloat(latStr));
    if (d < 0.01) { 
      if (!nodeToStations[nodeStr]) nodeToStations[nodeStr] = [];
      nodeToStations[nodeStr].push(station.properties.stationId);
    }
  }
});

const stationMap = {};
stations.forEach(s => { stationMap[s.properties.stationId] = s; });

const startStation = stations.find(s => s.properties.name === 'Jalandhar Cantonment Junction');
const startId = startStation.properties.stationId;

const startNodes = Object.keys(nodeToStations).filter(n => nodeToStations[n].includes(startId));
const queue = [...startNodes];
const visited = new Set(startNodes);
const connectedIds = new Set();

while (queue.length > 0) {
  const curr = queue.shift();
  let stopExploringBranch = false;
  
  if (nodeToStations[curr]) {
    for (const sid of nodeToStations[curr]) {
      if (sid !== startId) {
        connectedIds.add(sid);
        if (stationMap[sid].properties.stationClass === 'main') {
          stopExploringBranch = true;
        }
      }
    }
  }
  
  if (!stopExploringBranch) {
    for (const neighbor of graph[curr]) {
      if (!visited.has(neighbor)) {
        visited.add(neighbor);
        queue.push(neighbor);
      }
    }
  }
}

const mains = Array.from(connectedIds).map(id => stationMap[id]).filter(s => s.properties.stationClass === 'main');
console.log('Main stations connected:', mains.length);
console.log(mains.map(m => m.properties.name));
