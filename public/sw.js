// Service Worker - MatchDay PWA (Notifications Push & Mode Autonome)
const CACHE_NAME = 'matchday-cache-v21';

self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  // Suppression immédiate de tous les anciens caches pour éviter tout blocage
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(keys.map((key) => caches.delete(key)));
    })
  );
  self.clients.claim();
});

// Pas d'interception réseau agressive : le navigateur utilise directement le CDN Vercel sans latence
self.addEventListener('fetch', (e) => {
  return;
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
  const urlToOpen = event.notification.data?.url || './';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes('matchday') && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});
