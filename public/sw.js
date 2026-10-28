// Service Worker - MatchDay PWA
const CACHE_NAME = 'matchday-cache-v9';
const ASSETS = [
  './',
  './index.html',
  './styles.css',
  './app.js',
  './data.js',
  './licenses_registry.js',
  './manifest.json',
  './logo.png',
  './logos/logo_genech.png',
  './logos/logo_seclin.jpg',
  './qr_codes/qr_gnch.png',
  './qr_codes/qr_scln.png',
  './qr_codes/qr_root.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) return caches.delete(key);
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});

// -----------------------------------------------------------------------------
// GESTION DES NOTIFICATIONS NATIVES (WEB PUSH & LOCAL NOTIFICATIONS)
// -----------------------------------------------------------------------------

self.addEventListener('push', (event) => {
  let data = {
    title: 'MatchDay - Alerte Staff',
    body: 'Nouvelle information tactique ou disciplinaire FFF disponible.',
    icon: './logo.png'
  };

  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: data.icon || './logo.png',
    badge: './logo.png',
    vibrate: [200, 100, 200],
    data: {
      url: data.url || './'
    }
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes('match-day') && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(event.notification.data.url || './');
      }
    })
  );
});
