const fs = require('fs');
const path = require('path');
const outPath = 'public/stations_metadata.json';
const zones = JSON.parse(fs.readFileSync('public/zone_list.json'));

console.log('Loading geojson...');
const stations = [];
const tracks = [];

for (const zone of zones) {
  const data = JSON.parse(fs.readFileSync(`public/${zone}_real.geojson`));
  data.features.forEach((f) => {
    if (f.properties.type === 'station') {
      stations.push(f);
    } else if (f.properties.type === 'track') {
      tracks.push(f);
    }
  });
}


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

console.log('Building spatial grid...');
const grid = {};
for (const nodeStr of Object.keys(graph)) {
  const [lng, lat] = nodeStr.split(',').map(Number);
  const k = `${Math.floor(lng * 10)},${Math.floor(lat * 10)}`;
  if (!grid[k]) grid[k] = [];
  grid[k].push({ nodeStr, lng, lat });
}

console.log('Mapping stations to network with 1km radius wall...');
stations.forEach(station => {
  const p = station.geometry.coordinates;
  const kx = Math.floor(p[0] * 10);
  const ky = Math.floor(p[1] * 10);
  
  for (let i = -1; i <= 1; i++) {
    for (let j = -1; j <= 1; j++) {
       const k = `${kx + i},${ky + j}`;
       if (grid[k]) {
         for (const node of grid[k]) {
           const d = distance(p[0], p[1], node.lng, node.lat);
           if (d < 0.01) { 
             if (!nodeToStations[node.nodeStr]) nodeToStations[node.nodeStr] = [];
             nodeToStations[node.nodeStr].push(station.properties.stationId);
           }
         }
       }
    }
  }
});

const stationMap = {};
stations.forEach(s => { stationMap[s.properties.stationId] = s; });

const stationsMetadata = {};
let count = 0;

console.log('Running BFS for all stations to find paths and coords...');
stations.forEach(startStation => {
  const startId = startStation.properties.stationId;
  const startNodes = Object.keys(nodeToStations).filter(n => nodeToStations[n].includes(startId));
  
  const branches = [];
  
  if (startNodes.length > 0) {
    const queue = [...startNodes];
    const visited = new Set(startNodes);
    const parent = {};
    const mainStationsFound = new Set();
    
    while (queue.length > 0) {
      const curr = queue.shift();
      let stopExploringBranch = false;
      
      if (nodeToStations[curr]) {
        for (const sid of nodeToStations[curr]) {
          if (sid !== startId) {
            if (stationMap[sid].properties.stationClass === 'main') {
              stopExploringBranch = true;
              
              if (!mainStationsFound.has(sid)) {
                mainStationsFound.add(sid);
                const middleStationsOnPath = new Set();
                
                const destCoords = stationMap[sid].geometry.coordinates;
                const startCoords = startStation.geometry.coordinates;
                
                const coordsPath = [
                  destCoords.map(n => Math.round(n * 10000) / 10000),
                  curr.split(',').map(n => Math.round(Number(n) * 10000) / 10000)
                ];
                
                let p = parent[curr];
                let skipCount = 0;
                while (p) {
                  let isStationNode = false;
                  if (nodeToStations[p]) {
                    for (const midSid of nodeToStations[p]) {
                      if (midSid !== startId && midSid !== sid && stationMap[midSid].properties.stationClass === 'middle') {
                        middleStationsOnPath.add(midSid);
                        isStationNode = true;
                      }
                    }
                  }
                  
                  if (skipCount % 15 === 0 || isStationNode) {
                    coordsPath.push(p.split(',').map(n => Math.round(Number(n) * 10000) / 10000));
                  }
                  skipCount++;
                  p = parent[p];
                }
                coordsPath.push(startCoords.map(n => Math.round(n * 10000) / 10000));
                
                branches.push({ 
                  mainStationId: sid, 
                  middleStationIds: Array.from(middleStationsOnPath),
                  trackCoords: coordsPath.reverse()
                });
              }
            }
          }
        }
      }
      
      if (!stopExploringBranch) {
        for (const neighbor of graph[curr]) {
          if (!visited.has(neighbor)) {
            visited.add(neighbor);
            parent[neighbor] = curr;
            queue.push(neighbor);
          }
        }
      }
    }
  }
  
  stationsMetadata[startId] = {
    name: startStation.properties.name || 'Unknown',
    stationClass: startStation.properties.stationClass || 'middle',
    coordinates: startStation.geometry.coordinates,
    connectedBranches: branches
  };
  
  count++;
  if (count % 200 === 0) console.log(`Processed ${count}/${stations.length} stations`);
});

fs.writeFileSync(outPath, JSON.stringify(stationsMetadata));
console.log('Done mapping connections and saving metadata!');
