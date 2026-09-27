const fs = require('fs');
const timetable = JSON.parse(fs.readFileSync('./public/timetable.json'));
const origin = 'Jaipur Junction';
const dest = 'Bharatpur Junction';

const normalize = (name) => {
  if (!name) return '';
  return name.toLowerCase()
    .replace(/ junction| jn| cantt| cant| city| cb/g, '')
    .trim();
};

const normOrigin = normalize(origin);
const normDest = normalize(dest);
console.log('Norm Origin:', normOrigin, 'Norm Dest:', normDest);

let matches = 0;
for (const [tno, t] of Object.entries(timetable)) {
  const stops = t.s;
  let oIdx = -1;
  let dIdx = -1;
  
  for (let i = 0; i < stops.length; i++) {
    const sName = normalize(stops[i][0]);
    if (sName === normOrigin) oIdx = i;
    if (sName === normDest) dIdx = i;
  }
  
  if (oIdx !== -1 && dIdx !== -1 && oIdx < dIdx) {
    console.log(`Found Train: ${tno} - ${t.n}`);
    console.log(`  Departs ${stops[oIdx][0]} at ${stops[oIdx][2]}`);
    console.log(`  Arrives ${stops[dIdx][0]} at ${stops[dIdx][1]}`);
    matches++;
  }
}
console.log(`Total matches: ${matches}`);
