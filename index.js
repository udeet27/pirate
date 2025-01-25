const Client = require("utorrent-api");

// Retrieve the magnet link from the command-line arguments
const magnetLink = process.argv[2];

if (!magnetLink) {
  console.error("Error: No magnet link provided!");
  console.error("Usage: node index.js <magnetLink>");
  process.exit(1);
}

// Initialize uTorrent client
const utorrent = new Client("localhost", "26112");
utorrent.setCredentials("admin", "1234");

// Use the `add-url` method to add the magnet link
utorrent.call("add-url", { s: magnetLink }, function (err, data) {
  if (err) {
    console.error("Error adding torrent:");
    console.error(err);
    return;
  }

  console.log("Successfully added torrent!");
  console.log(data);
});
