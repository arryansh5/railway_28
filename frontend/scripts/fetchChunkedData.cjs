const axios = require('axios');
const osmtogeojson = require('osmtogeojson');
const fs = require('fs');
const path = require('path');

const OVERPASS_URL = 'https://overpass-api.de/api/interpreter';

// Delhi NCR Bounding Box: 28.0, 76.0 to 29.5, 78.0
const MIN_LAT = 28.0;
const MIN_LON = 76.0;
const MAX_LAT = 29.5;
const MAX_LON = 78.0;
const STEP = 0.5; // 0.5 degree chunks

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function fetchChunk(minLat, minLon, maxLat, maxLon) {
  const bbox = `${minLat},${minLon},${maxLat},${maxLon}`;
  const query = `
    [out:json][timeout:25];
    (
      way["railway"="rail"](${bbox});
      node["railway"="station"](${bbox});
    );
    out body;
    >;
    out skel qt;
  `;

  try {
    const response = await axios.post(OVERPASS_URL, `data=${encodeURIComponent(query)}`, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'ChunkedRailwayFetcher/1.0 (test@example.com)'
      },
      timeout: 30000
    });
    return osmtogeojson(response.data).features || [];
  } catch (e) {
    console.error(`Chunk [${bbox}] failed: ${e.message}`);
    return [];
  }
}

async function fetchAll() {
  console.log('Fetching railway data in chunks to avoid timeouts...');
  let allFeatures = [];
  let totalChunks = 0;
  let currentChunk = 0;

  for (let lat = MIN_LAT; lat < MAX_LAT; lat += STEP) {
    for (let lon = MIN_LON; lon < MAX_LON; lon += STEP) {
      totalChunks++;
    }
  }

  for (let lat = MIN_LAT; lat < MAX_LAT; lat += STEP) {
    for (let lon = MIN_LON; lon < MAX_LON; lon += STEP) {
      currentChunk++;
      const nextLat = Math.min(lat + STEP, MAX_LAT);
      const nextLon = Math.min(lon + STEP, MAX_LON);
      console.log(`Fetching chunk ${currentChunk}/${totalChunks} (Lat: ${lat.toFixed(2)} to ${nextLat.toFixed(2)}, Lon: ${lon.toFixed(2)} to ${nextLon.toFixed(2)})...`);
      
      const features = await fetchChunk(lat, lon, nextLat, nextLon);
      allFeatures = allFeatures.concat(features);
      
      // Wait 1.5 seconds between chunks to avoid rate limiting
      await sleep(1500);
    }
  }

  // Deduplicate features by ID
  const uniqueFeatures = [];
  const seenIds = new Set();
  
  for (const feature of allFeatures) {
    if (!seenIds.has(feature.id)) {
      seenIds.add(feature.id);
      
      // Optimize feature
      const isStation = feature.geometry.type === 'Point';
      uniqueFeatures.push({
        type: 'Feature',
        geometry: feature.geometry,
        properties: {
          id: feature.id,
          type: isStation ? 'station' : 'track',
          name: feature.properties.name || null,
        }
      });
    }
  }

  const geojson = {
    type: 'FeatureCollection',
    features: uniqueFeatures
  };

  const outputPath = path.join(__dirname, '../public/northern_railway_real.geojson');
  fs.writeFileSync(outputPath, JSON.stringify(geojson));
  console.log(`\nSuccessfully saved ${uniqueFeatures.length} unique features to ${outputPath}`);
}

fetchAll();
