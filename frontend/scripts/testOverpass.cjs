const axios = require('axios');
const fs = require('fs');

async function testOverpass() {
  const query = `
    [out:json][timeout:25];
    (
      way["railway"="rail"](28.4, 76.8, 28.9, 77.5);
      node["railway"="station"](28.4, 76.8, 28.9, 77.5);
    );
    out body;
    >;
    out skel qt;
  `;
  
  try {
    const res = await axios.post('https://overpass.kumi.systems/api/interpreter', query, {
      headers: { 'Content-Type': 'text/plain' }
    });
    console.log("Success! Data size:", JSON.stringify(res.data).length);
    fs.writeFileSync('test_data.json', JSON.stringify(res.data));
  } catch (err) {
    console.error("Failed:", err.message);
    if (err.response) {
      console.error(err.response.status, err.response.data);
    }
  }
}

testOverpass();
