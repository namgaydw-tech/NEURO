const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = parseInt(process.env.PORT || '3001', 10);
const ROOT = __dirname;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.js':   'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif':  'image/gif',
  '.svg':  'image/svg+xml',
  '.ico':  'image/x-icon',
  '.woff': 'font/woff',
  '.woff2':'font/woff2',
};

function serve(req, res) {
  let url = decodeURIComponent(req.url.split('?')[0]);

  // Serve Clerk config as JavaScript (publishable key is safe to expose)
  if (url === '/config.js') {
    const fs2 = require('fs');
    let publishableKey = '';
    try {
      const envContent = fs2.readFileSync(path.join(ROOT, '.env'), 'utf8');
      const match = envContent.match(/^CLERK_PUBLISHABLE_KEY=(.*)$/m);
      if (match) publishableKey = match[1].trim();
    } catch(e) {}
    res.writeHead(200, { 'Content-Type': 'application/javascript; charset=utf-8' });
    res.end(`window.__CLERK_PUBLISHABLE_KEY = ${JSON.stringify(publishableKey)};\n`);
    return;
  }

  if (url === '/') url = '/index.html';

  // Prevent directory traversal
  const safe = path.normalize(url).replace(/^(\.\.[\/\\])+/, '');
  const filePath = path.join(ROOT, safe);

  // Security: ensure resolved path is under ROOT
  if (!filePath.startsWith(ROOT)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

  fs.stat(filePath, (err, stat) => {
    if (err || !stat.isFile()) {
      res.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end('<h1>404 Not Found</h1>');
      return;
    }
    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME[ext] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': contentType });
    fs.createReadStream(filePath).pipe(res);
  });
}

const server = http.createServer(serve);
server.listen(PORT, '127.0.0.1', () => {
  console.log(`NEURO_PREDICT_SYS preview running at http://127.0.0.1:${PORT}`);
});
