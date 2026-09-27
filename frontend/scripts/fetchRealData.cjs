const axios = require('axios');
const osmtogeojson = require('osmtogeojson');
const fs = require('fs');
const path = require('path');

// Using Kumi Systems Overpass instance which handles large queries better
const OVERPASS_URL = 'https://overpass.kumi.systems/api/interpreter';

// Bounding box for Delhi NCR and surrounding areas to avoid server timeout
// min_lat, min_lon, max_lat, max_lon
const BBOX = '28.0,76.0,29.5,78.0';

const query = `
  [out:json][timeout:300];
  (
    way["railway"="rail"](${BBOX});
    node["railway"="station"](${BBOX});
  );
  out body;
  >;
  out skel qt;
`;

async function fetchRealData() {
  console.log('Fetching massive real-world railway data from Overpass API (this may take 2-3 minutes)...');
  try {
    const response = await axios.post(OVERPASS_URL, query, {
      headers: {
        'Content-Type': 'text/plain',
        'User-Agent': 'NorthernRailwayTracker/1.0 (contact@example.com) Axios/1.7.0'
      },
      timeout: 300000 // 5 minutes
    });

    console.log('Data fetched! Converting OSM JSON to GeoJSON...');
    
    // Convert OSM JSON to GeoJSON
    const geojson = osmtogeojson(response.data);
    
    // Optimize GeoJSON: Keep only useful properties to reduce file size and rendering lag
    geojson.features = geojson.features.map(feature => {
      const isStation = feature.geometry.type === 'Point';
      return {
        type: 'Feature',
        geometry: feature.geometry,
        properties: {
          id: feature.id,
          type: isStation ? 'station' : 'track',
          name: feature.properties.name || null,
        }
      };
    });

    const outputPath = path.join(__dirname, '../public/northern_railway_real.geojson');
    fs.writeFileSync(outputPath, JSON.stringify(geojson));
    
    console.log(`Successfully saved real GeoJSON to ${outputPath}`);
    console.log(`Total Features: ${geojson.features.length}`);
  } catch (error) {
    console.error('Error fetching data:', error.message);
    if (error.response) {
      console.error(error.response.status, error.response.data);
    }
  }
}

fetchRealData();
