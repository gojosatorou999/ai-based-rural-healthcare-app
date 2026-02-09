// Service Worker for Pristin Healthcare PWA
// Provides offline-first functionality for rural telemedicine

const CACHE_VERSION = 'v1.0.0';
const STATIC_CACHE = `pristin-static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `pristin-dynamic-${CACHE_VERSION}`;
const DATA_CACHE = `pristin-data-${CACHE_VERSION}`;

// Static assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/dashboard',
  '/static/css/style.css',
  '/static/js/app.js',
  '/static/manifest.json',
  'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
  'https://cdn.plot.ly/plotly-latest.min.js'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Service Worker...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating Service Worker...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames
          .filter(name => name !== STATIC_CACHE && name !== DYNAMIC_CACHE && name !== DATA_CACHE)
          .map(name => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache with network fallback
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  // API calls - network first with cache fallback
  if (url.pathname.startsWith('/api/') || url.pathname.includes('/new_')) {
    event.respondWith(networkFirstStrategy(event.request));
    return;
  }

  // Static assets - cache first
  if (isStaticAsset(url.pathname)) {
    event.respondWith(cacheFirstStrategy(event.request));
    return;
  }

  // HTML pages - stale while revalidate
  if (event.request.headers.get('accept').includes('text/html')) {
    event.respondWith(staleWhileRevalidate(event.request));
    return;
  }

  // Default - network first
  event.respondWith(networkFirstStrategy(event.request));
});

// Check if request is for static asset
function isStaticAsset(pathname) {
  return pathname.includes('/static/') ||
    pathname.includes('.css') ||
    pathname.includes('.js') ||
    pathname.includes('.png') ||
    pathname.includes('.jpg') ||
    pathname.includes('.woff');
}

// Cache-first strategy
async function cacheFirstStrategy(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    const cache = await caches.open(STATIC_CACHE);
    cache.put(request, networkResponse.clone());
    return networkResponse;
  } catch (error) {
    return new Response('Offline - resource not cached', { status: 503 });
  }
}

// Network-first strategy
async function networkFirstStrategy(request) {
  try {
    const networkResponse = await fetch(request);
    const cache = await caches.open(DYNAMIC_CACHE);
    cache.put(request, networkResponse.clone());
    return networkResponse;
  } catch (error) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    return new Response(JSON.stringify({ error: 'Offline' }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Stale-while-revalidate strategy
async function staleWhileRevalidate(request) {
  const cache = await caches.open(DYNAMIC_CACHE);
  const cachedResponse = await cache.match(request);

  const fetchPromise = fetch(request)
    .then(networkResponse => {
      cache.put(request, networkResponse.clone());
      return networkResponse;
    })
    .catch(() => cachedResponse || new Response('Offline', { status: 503 }));

  return cachedResponse || fetchPromise;
}

// Background sync for offline data
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);

  if (event.tag === 'sync-vitals') {
    event.waitUntil(syncVitalsData());
  }
  if (event.tag === 'sync-symptoms') {
    event.waitUntil(syncSymptomsData());
  }
});

// Sync vitals data when back online
async function syncVitalsData() {
  try {
    const pendingVitals = await getPendingData('pending-vitals');
    for (const vital of pendingVitals) {
      await fetch('/new_vital_record', {
        method: 'POST',
        body: new URLSearchParams(vital),
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
    }
    await clearPendingData('pending-vitals');
  } catch (error) {
    console.error('[SW] Sync vitals failed:', error);
  }
}

// Sync symptoms data when back online  
async function syncSymptomsData() {
  try {
    const pendingSymptoms = await getPendingData('pending-symptoms');
    for (const symptom of pendingSymptoms) {
      await fetch('/new_symptom_report', {
        method: 'POST',
        body: new URLSearchParams(symptom),
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
    }
    await clearPendingData('pending-symptoms');
  } catch (error) {
    console.error('[SW] Sync symptoms failed:', error);
  }
}

// Helper to get pending data from IndexedDB (via postMessage)
async function getPendingData(storeName) {
  // This will be implemented via message passing from the main app
  return [];
}

async function clearPendingData(storeName) {
  // This will be implemented via message passing from the main app
}

// Push notifications for appointments and alerts
self.addEventListener('push', (event) => {
  const data = event.data?.json() || { title: 'Health Alert', body: 'You have a new notification' };

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/static/icons/icon-192.png',
      badge: '/static/icons/badge-72.png',
      vibrate: [200, 100, 200],
      tag: data.tag || 'health-notification',
      actions: data.actions || []
    })
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  event.waitUntil(
    clients.openWindow(event.notification.data?.url || '/dashboard')
  );
});

console.log('[SW] Service Worker loaded');
