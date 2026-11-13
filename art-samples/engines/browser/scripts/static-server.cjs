// Tiny dependency-free static file server. `mounts` maps URL prefixes to directories
// (or exact URL paths to files); the longest matching prefix wins.
const http = require('http');
const fs = require('fs');
const path = require('path');

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.webp': 'image/webp', '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.map': 'application/json',
};

function startServer(mounts, port = 0, host = '127.0.0.1') {
  const entries = Object.entries(mounts).sort((a, b) => b[0].length - a[0].length);
  const server = http.createServer((req, res) => {
    const urlPath = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    for (const [prefix, target] of entries) {
      if (urlPath !== prefix && !(prefix.endsWith('/') && urlPath.startsWith(prefix))) continue;
      let file = prefix.endsWith('/') ? path.join(target, urlPath.slice(prefix.length)) : target;
      if (prefix.endsWith('/') && !file.startsWith(path.resolve(target))) break; // traversal
      if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
      if (!fs.existsSync(file)) break;
      res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-cache' });
      fs.createReadStream(file).pipe(res);
      return;
    }
    res.writeHead(404); res.end('not found: ' + urlPath);
  });
  return new Promise((resolve) => server.listen(port, host, () => resolve(server)));
}

module.exports = { startServer };

// CLI: node static-server.cjs <dir> [port]  — serve a folder (e.g. the bundled site/).
if (require.main === module) {
  const dir = path.resolve(process.argv[2] || '.');
  startServer({ '/': dir }, Number(process.argv[3] || 8080), '0.0.0.0').then((s) =>
    console.log(`serving ${dir} at http://localhost:${s.address().port}/`));
}
