const fs = require('fs');
const path = require('path');
const publicDir = 'public';

const zones = JSON.parse(fs.readFileSync(path.join(publicDir, 'zone_list.json')));

// Major station keywords that must match as whole words
const exactKeywords = ['Jn', 'Junction', 'Central', 'Cantt', 'Cantt.', 'Terminus', 'Terminal'];

const majorCities = [
  'Delhi', 'New Delhi', 'Lucknow', 'Amritsar', 'Chandigarh', 'Ludhiana', 
  'Saharanpur', 'Moradabad', 'Bareilly', 'Ambala', 'Jammu', 'Bathinda', 
  'Katra', 'Haridwar', 'Dehradun', 'Shimla', 'Meerut', 'Agra', 'Kanpur', 
  'Mathura', 'Varanasi', 'Banaras', 'Roorkee', 'Panipat', 'Sonipat', 
  'Kurukshetra', 'Karnal', 'Rohtak', 'Hisar', 'Bikaner', 'Jodhpur', 
  'Jaipur', 'Ajmer', 'Kota', 'Gwalior', 'Jhansi', 'Aligarh', 'Ghaziabad',
  'Faridabad', 'Gurgaon', 'Noida'
];

let globalIndex = 0;
let mainCount = 0;
let middleCount = 0;
const mainStationNames = new Set();

for (const zone of zones) {
  const geojsonPath = path.join(publicDir, `${zone}_real.geojson`);
  const data = JSON.parse(fs.readFileSync(geojsonPath));
  
  data.features.forEach((f) => {
    if (f.properties.type === 'station') {
      f.properties.stationId = `station_${globalIndex++}`;
      const name = f.properties.name || '';
      let isMain = false;
      
      for (const kw of exactKeywords) {
        const safeKw = kw.replace('.', '\\.');
        const regex = new RegExp(`\\b${safeKw}\\b`, 'i');
        if (regex.test(name)) {
          isMain = true;
          break;
        }
      }

      if (!isMain) {
        for (const city of majorCities) {
          if (name.toLowerCase().includes(city.toLowerCase())) {
            isMain = true;
            break;
          }
        }
      }
      
      if (isMain) {
        f.properties.stationClass = 'main';
        mainStationNames.add(name);
        mainCount++;
      } else {
        f.properties.stationClass = 'middle';
        middleCount++;
      }
    }
  });
  
  fs.writeFileSync(geojsonPath, JSON.stringify(data));
  console.log(`Processed stations for ${zone}`);
}

const sortedMain = Array.from(mainStationNames).sort();
console.log("MAIN_COUNT:" + mainCount);
console.log("MIDDLE_COUNT:" + middleCount);
