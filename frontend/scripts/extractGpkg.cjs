const Database = require('better-sqlite3');
const wkx = require('wkx');
const fs = require('fs');
const path = require('path');

const publicDir = path.join(__dirname, '../public');

function parseGPKGBlob(blob) {
  if (!blob || blob.length < 8) return null;
  if (blob[0] !== 0x47 || blob[1] !== 0x50) return null;
  
  const flags = blob[3];
  const envelopeIndicator = (flags >> 1) & 7;
  
  let headerSize = 8;
  if (envelopeIndicator === 1) headerSize += 32;
  else if (envelopeIndicator === 2 || envelopeIndicator === 3) headerSize += 48;
  else if (envelopeIndicator === 4) headerSize += 64;
  
  const wkbBuffer = blob.slice(headerSize);
  try {
    const geometry = wkx.Geometry.parse(wkbBuffer);
    return geometry.toGeoJSON();
  } catch (e) {
    console.error("WKB Parse error:", e);
    return null;
  }
}

// Get all .gpkg files in public directory
const gpkgFiles = fs.readdirSync(publicDir).filter(f => f.endsWith('.gpkg'));
console.log(`Found ${gpkgFiles.length} GeoPackage files.`);

const allZones = [];

for (const gpkgFile of gpkgFiles) {
  const gpkgPath = path.join(publicDir, gpkgFile);
  const zoneName = gpkgFile.replace('.gpkg', '');
  const outPath = path.join(publicDir, `${zoneName}_real.geojson`);
  console.log(`\nProcessing GeoPackage: ${gpkgFile}`);
  
  const features = [];
  try {
    const db = new Database(gpkgPath, { readonly: true });
    const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all();
    
    if (tables.some(t => t.name === 'gis_osm_railways_free')) {
      const lines = db.prepare("SELECT geom, fclass, name FROM gis_osm_railways_free WHERE fclass='rail'").all();
      console.log(`  - Found ${lines.length} main rail segments.`);
      lines.forEach(row => {
        const geom = parseGPKGBlob(row.geom);
        if (geom) features.push({ type: 'Feature', geometry: geom, properties: { type: 'track', name: row.name, fclass: row.fclass } });
      });
    }

    if (tables.some(t => t.name === 'gis_osm_transport_free')) {
      const points = db.prepare("SELECT geom, fclass, name FROM gis_osm_transport_free WHERE fclass IN ('railway_station', 'railway_halt')").all();
      console.log(`  - Found ${points.length} stations/halts.`);
      points.forEach(row => {
        const geom = parseGPKGBlob(row.geom);
        if (geom) features.push({ type: 'Feature', geometry: geom, properties: { type: 'station', name: row.name, fclass: row.fclass } });
      });
    }
    db.close();
    
    fs.writeFileSync(outPath, JSON.stringify({ type: 'FeatureCollection', features }));
    console.log(`  - Saved ${outPath}`);
    allZones.push(zoneName);
  } catch (e) {
    console.error(`Error processing ${gpkgFile}:`, e.message);
  }
}

// Save a list of zones for the frontend to load
fs.writeFileSync(path.join(publicDir, 'zone_list.json'), JSON.stringify(allZones));
console.log(`\nSuccess! Extracted all zones separately.`);
