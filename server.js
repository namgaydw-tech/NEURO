const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');

const PORT = parseInt(process.env.PORT || '3000', 10);
const ROOT = __dirname;
const USE_HTTPS = process.env.HTTPS !== 'false';

// ── MIME types ──────────────────────────────────────────────────
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
  '.webp': 'image/webp',
  '.woff2':'font/woff2',
};

// ── Request handler ─────────────────────────────────────────────
function serve(req, res) {
  let url = decodeURIComponent(req.url.split('?')[0]);

  // Security headers
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');

  // Serve Clerk config
  if (url === '/config.js') {
    let publishableKey = '';
    try {
      const envContent = fs.readFileSync(path.join(ROOT, '.env'), 'utf8');
      const match = envContent.match(/^CLERK_PUBLISHABLE_KEY=(.*)$/m);
      if (match) publishableKey = match[1].trim();
    } catch(e) {}
    // Generate config.js: Clerk key + dynamic loader (only load SDK when key exists)
    const clerkLoader = publishableKey ? (
      `(function(){var s=document.createElement('script');s.src='https://cdn.jsdelivr.net/npm/@clerk/clerk-js@latest/dist/clerk.browser.js';s.async=true;s.onerror=function(){console.warn('[Config] Failed to load Clerk SDK')};document.head.appendChild(s)})()`
    ) : (`console.info('[Config] No Clerk publishable key - using legacy JWT auth')`);
    res.writeHead(200, { 'Content-Type': 'application/javascript; charset=utf-8' });
    res.end(`window.__CLERK_PUBLISHABLE_KEY = ${JSON.stringify(publishableKey)};\n${clerkLoader}\n`);
    return;
  }

  // Root → index.html
  if (url === '/') url = '/index.html';

  // Clean URL fallback: /foo → /foo.html
  const safe = path.normalize(url).replace(/^(\.\.[\/\\])+/, '');
  const filePath = path.join(ROOT, safe);

  if (!filePath.startsWith(ROOT)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

  fs.stat(filePath, (err, stat) => {
    // Try .html fallback for clean URLs
    if ((err || !stat.isFile()) && !path.extname(filePath)) {
      try {
        const htmlStat = fs.statSync(filePath + '.html');
        if (htmlStat.isFile()) {
          res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
          fs.createReadStream(filePath + '.html').pipe(res);
          return;
        }
      } catch(e) {}
    }

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

// ── Start server ────────────────────────────────────────────────
if (USE_HTTPS) {
  const certPath = path.join(__dirname, 'certs', 'cert.pem');
  const keyPath = path.join(__dirname, 'certs', 'key.pem');

  if (fs.existsSync(certPath) && fs.existsSync(keyPath)) {
    const options = {
      key: fs.readFileSync(keyPath),
      cert: fs.readFileSync(certPath),
    };
    https.createServer(options, serve).listen(PORT, '127.0.0.1', () => {
      console.log(`\n  🔒 NEURO_PREDICT_SYS running at https://127.0.0.1:${PORT}`);
      console.log(`  📱 Landing: https://127.0.0.1:${PORT}/`);
      console.log(`  📊 Dashboard: https://127.0.0.1:${PORT}/global_neural_dashboard_v1/code.html`);
      console.log(`  🧠 AI Analysis: https://127.0.0.1:${PORT}/ai_analysis/code.html\n`);
    });
  } else {
    console.warn('⚠️  SSL certs not found, falling back to HTTP');
    http.createServer(serve).listen(PORT, '127.0.0.1', () => {
      console.log(`\n  NEURO_PREDICT_SYS running at http://127.0.0.1:${PORT}\n`);
    });
  }
} else {
  http.createServer(serve).listen(PORT, '127.0.0.1', () => {
    console.log(`\n  NEURO_PREDICT_SYS running at http://127.0.0.1:${PORT}\n`);
  });
}
