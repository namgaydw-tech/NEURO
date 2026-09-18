// NEURO_PREDICT_SYS - Service Worker
// Handles offline caching and background sync

const CACHE_NAME = 'neuro-predict-v2';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/config.js',
  '/landing/index.html',
  '/app/dashboard.html',
  '/app/dashboard.js',
  '/shared/design-system.css',
  '/shared/layout.css',
  '/shared/layout.js',
  '/shared/ui.js',
  '/shared/auth.js',
  '/shared/api.js'
];

// Files to cache from each module
const MODULE_PATHS = [
  '/app/dashboard.html',
  '/landing/index.html',
  '/3fa_pharmacy_login/code.html',
  '/ot_scheduling_login/code.html',
  '/global_neural_dashboard_v1/code.html',
  '/pharmacist_login/code.html',
  '/neurosurgery_login/code.html',
  '/medical_history_login/code.html',
  '/ai_analysis/code.html',
  '/final_diagnosis_report_v1/code.html',
  '/neural_archive_eeg_interpreter/code.html',
  '/prediction_command_center_v1/code.html',
  '/research_papers_1/code.html',
  '/research_papers_2/code.html'
];

// External resources to cache
const EXTERNAL_RESOURCES = [
  'https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&family=Inter:wght@400;500;600&family=Space+Grotesk:wght@300;400;500;700&display=swap',
  'https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap',
  'https://cdn.jsdelivr.net/npm/@clerk/clerk-js@latest/dist/clerk.browser.js',
  'https://cdn.tailwindcss.com?plugins=forms,container-queries'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Caching static assets');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip API calls (they need network)
  if (url.pathname.startsWith('/api/')) {
    return;
  }

  // Skip external resources for now (they might change)
  if (url.origin !== self.location.origin) {
    // For external resources, try network first, cache if fails
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone and cache successful responses
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, clone);
            });
          }
          return response;
        })
        .catch(() => {
          // Return placeholder for failed external resources
          if (url.pathname.includes('fonts.googleapis.com') || url.pathname.includes('cdn.tailwindcss.com')) {
            return new Response('', { status: 200, headers: { 'Content-Type': 'text/css' } });
          }
          return caches.match(request).then((cached) => {
            return cached || new Response('Offline', { status: 503 });
          });
        })
    );
    return;
  }

  // For module HTML pages, try cache first, then network
  if (MODULE_PATHS.some((path) => url.pathname.endsWith(path) || url.pathname === path)) {
    event.respondWith(
      caches.match(request).then((cached) => {
        return cached || fetch(request).then((response) => {
          // Cache the response for future use
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, clone);
          });
          return response;
        }).catch(() => {
          // Return offline page or cached version
          return caches.match('/index.html');
        });
      })
    );
    return;
  }

  // For other requests, use network first, fall back to cache
  event.respondWith(
    fetch(request)
      .then((response) => {
        // Cache successful responses
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, clone);
          });
        }
        return response;
      })
      .catch(() => {
        return caches.match(request).then((cached) => {
          return cached || new Response('Offline', { status: 503 });
        });
      })
  );
});

// Background sync for API calls when back online
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-api-calls') {
    event.waitUntil(syncApiCalls());
  }
});

async function syncApiCalls() {
  // Get pending API calls from IndexedDB
  // This is a simplified version - in production, you'd use a proper queue
  console.log('[SW] Syncing pending API calls');
  // Implementation would go here for production use
}

// Push notifications (for future use)
self.addEventListener('push', (event) => {
  if (!event.data) return;

  const data = event.data.json();
  const options = {
    body: data.body || 'New notification',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      url: data.url || '/'
    }
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'NEURO_PREDICT_SYS', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then((clientList) => {
      for (const client of clientList) {
        if (client.url === event.notification.data.url && 'focus' in client) {
          return client.focus();
        }
      }
      return clients.openWindow(event.notification.data.url);
    })
  );
});
