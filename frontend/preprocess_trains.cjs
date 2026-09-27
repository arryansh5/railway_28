const fs = require('fs');
const csv = require('csv-parser');

const inputFile = './public/ir_train.csv';
const outputFile = './public/trains_summary.json';

const trains = {};

console.log('Processing ir_train.csv...');

let rowCount = 0;

fs.createReadStream(inputFile)
  .pipe(csv())
  .on('data', (data) => {
    rowCount++;
    if (rowCount % 500000 === 0) {
      console.log(`Processed ${rowCount} rows...`);
    }

    const trainNo = data.train_number;
    if (!trainNo) return;

    if (!trains[trainNo]) {
      trains[trainNo] = {
        train_number: trainNo,
        train_type: data.train_type,
        source_category: data.source_station_category,
        dest_category: data.destination_station_category,
        total_journeys: 0,
        total_delay: 0,
        total_distance: 0,
      };
    }

    trains[trainNo].total_journeys += 1;
    trains[trainNo].total_delay += parseFloat(data.delay_minutes) || 0;
    trains[trainNo].total_distance += parseFloat(data.distance_km) || 0;
  })
  .on('end', () => {
    console.log(`Finished processing ${rowCount} rows.`);
    
    // Compute averages
    const summaryList = Object.values(trains).map(t => ({
      train_number: t.train_number,
      train_type: t.train_type,
      source_category: t.source_category,
      dest_category: t.dest_category,
      avg_delay_minutes: Math.round(t.total_delay / t.total_journeys),
      distance_km: Math.round(t.total_distance / t.total_journeys)
    }));

    console.log(`Found ${summaryList.length} unique trains.`);

    fs.writeFileSync(outputFile, JSON.stringify(summaryList, null, 2));
    console.log(`Saved summary to ${outputFile}`);
  });
