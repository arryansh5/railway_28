const fs = require('fs');

const path = 'public/northern_railway_real.geojson';
const outPath = 'public/stations_metadata.json';
console.log('Loading geojson...');
const data = JSON.parse(fs.readFileSync(path));

const stationsMetadata = {};

data.features.forEach((f) => {
  if (f.properties.type === 'station') {
    const id = f.properties.stationId;
    if (id) {
      stationsMetadata[id] = {
        name: f.properties.name || 'Unknown',
        stationClass: f.properties.stationClass || 'middle',
        connectedStations: f.properties.connectedStations || []
      };
    }
  }
});

console.log(`Writing metadata for ${Object.keys(stationsMetadata).length} stations...`);
fs.writeFileSync(outPath, JSON.stringify(stationsMetadata));
console.log('Done!');
