const fs = require('fs');
const path = require('path');
const osmtogeojson = require('osmtogeojson');

async function testFetch() {
  const bbox = '28.5,77.0,28.8,77.4'; // Just Delhi
  const query = `[out:json][timeout:25];(way["railway"="rail"](${bbox});node["railway"="station"](${bbox}););out body;>;out skel qt;`;
  
  const url = `https://overpass-api.de/api/interpreter?data=${encodeURIComponent(query)}`;
  
  console.log("Fetching from:", url);
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' // Pretend to be a browser
      }
    });
    
    if (!response.ok) {
      console.log(`Failed! Status: ${response.status}`);
      const text = await response.text();
      console.log(text.substring(0, 200));
      return;
    }
    
    const data = await response.json();
    console.log("Success! Data points:", data.elements.length);
    
    const geojson = osmtogeojson(data);
    const outputPath = path.join(__dirname, '../public/northern_railway_real.geojson');
    fs.writeFileSync(outputPath, JSON.stringify(geojson));
    console.log("Saved geojson to:", outputPath);
    
  } catch (err) {
    console.log("Network error:", err.message);
  }
}

testFetch();
