// NEURO_PREDICT_SYS - Service Worker
// Static assets ONLY — never cache API responses, auth tokens, or patient data.

const CACHE_NAME = 'neuro-predict-v3';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/config.js',
  '/shared/auth.js',
  '/shared/api.js',
  '/shared/ui.js',
  '/shared/profile-panel.js',
  '/shared/styles.css',
];

// Install — cache only safe static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Caching static assets');
      return Promise.allSettled(
        STATIC_ASSETS.map(url => cache.add(url).catch(e => {
          console.warn(`[SW] Failed to cache ${url}:`, e.message);
        }))
      );
    })
  );
  self.skipWaiting();
});

// Activate — clean old caches
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

// Fetch — network-first for everything, cache-only for known-safe static assets
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // NEVER cache: API calls, auth, tokens, patient data, WebSocket
  if (
    request.method !== 'GET' ||
    url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/ws/') ||
    url.pathname.includes('/auth/') ||
    url.pathname.includes('/patients') ||
    url.pathname.includes('/diagnoses') ||
    url.pathname.includes('/analysis') ||
    url.pathname.includes('/eeg') ||
    url.pathname.includes('/medications') ||
    url.pathname.includes('/pharmacy') ||
    url.pathname.includes('/ot/') ||
    url.pathname.includes('/research') ||
    url.pathname.includes('/dashboard/') ||
    url.pathname.includes('/system/') ||
    url.pathname.includes('/health') ||
    url.pathname.includes('/users/')
  ) {
    return; // Let browser handle normally — no caching
  }

  // For external CDN resources (fonts, Tailwind, Clerk) — stale-while-revalidate
  if (url.origin !== self.location.origin) {
    event.respondWith(
      caches.open(CACHE_NAME).then(async (cache) => {
        try {
          const networkResponse = await fetch(request);
          if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
          }
          return networkResponse;
        } catch {
          const cached = await cache.match(request);
          return cached || new Response('', { status: 503 });
        }
      })
    );
    return;
  }

  // For local static assets — cache-first, then network
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, clone);
          });
        }
        return response;
      }).catch(() => {
        return new Response('Offline', { status: 503 });
      });
    })
  );
});

// Push notifications (future)
self.addEventListener('push', (event) => {
  if (!event.data) return;
  const data = event.data.json();
  event.waitUntil(
    self.registration.showNotification(data.title || 'NEURO_PREDICT_SYS', {
      body: data.body || 'New notification',
      icon: '/icons/icon-192x192.png',
      badge: '/icons/badge-72x72.png',
      vibrate: [100, 50, 100],
      data: { url: data.url || '/' },
    })
  );
});

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
