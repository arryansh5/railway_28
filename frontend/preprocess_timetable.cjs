const fs = require('fs');
const csv = require('csv-parser');

const inputFile = './public/isl_wise_train_detail_03082015_v1.csv';
const outputFile = './public/timetable.json';

const trains = {};

console.log('Processing timetable...');

// Function to clean quotes
const clean = (str) => {
  if (!str) return '';
  return str.replace(/^'|'$/g, '').trim();
};

fs.createReadStream(inputFile)
  .pipe(csv())
  .on('data', (data) => {
    const trainNo = clean(data['Train No.']);
    if (!trainNo) return;

    if (!trains[trainNo]) {
      trains[trainNo] = {
        n: clean(data['train Name']),
        s: [] // stops
      };
    }

    trains[trainNo].s.push({
      i: parseInt(clean(data['islno']), 10) || 0,
      name: clean(data['Station Name']),
      arr: clean(data['Arrival time']),
      dep: clean(data['Departure time']),
      dist: parseInt(clean(data['Distance']), 10) || 0
    });
  })
  .on('end', () => {
    console.log(`Finished processing CSV.`);
    
    // Sort stops and format output
    const formatted = {};
    for (const [tno, tData] of Object.entries(trains)) {
      tData.s.sort((a, b) => a.i - b.i); // Sort by islno
      // Convert to smaller array format for stops: [name, arr, dep, dist]
      formatted[tno] = {
        n: tData.n,
        s: tData.s.map(stop => [stop.name, stop.arr, stop.dep, stop.dist])
      };
    }

    console.log(`Found ${Object.keys(formatted).length} unique trains.`);

    fs.writeFileSync(outputFile, JSON.stringify(formatted));
    console.log(`Saved timetable to ${outputFile}`);
  });
