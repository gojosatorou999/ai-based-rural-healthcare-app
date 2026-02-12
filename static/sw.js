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
  '/offline',
  '/symptom_input',
  '/vitals_input',
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

  // HTML pages - stale while revalidate with offline fallback
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

// Stale-while-revalidate strategy with offline fallback
async function staleWhileRevalidate(request) {
  const cache = await caches.open(DYNAMIC_CACHE);
  const cachedResponse = await cache.match(request);

  const fetchPromise = fetch(request)
    .then(networkResponse => {
      cache.put(request, networkResponse.clone());
      return networkResponse;
    })
    .catch(async () => {
      if (cachedResponse) return cachedResponse;

      // Fallback to offline page
      const staticCache = await caches.open(STATIC_CACHE);
      const offlineResponse = await staticCache.match('/offline');
      return offlineResponse || new Response('Offline', { status: 503 });
    });

  return cachedResponse || fetchPromise;
}

// Background sync for offline data
// Background sync for offline data
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);

  if (event.tag === 'sync-vitals') {
    event.waitUntil(syncVitalsData());
  } else if (event.tag === 'sync-symptoms') {
    event.waitUntil(syncSymptomsData());
  } else if (event.tag === 'sync-prescriptions') {
    event.waitUntil(syncPrescriptionsData());
  }
});

// Sync vitals data when back online
async function syncVitalsData() {
  try {
    const pendingVitals = await getPendingData('pending_vitals');
    if (!pendingVitals || pendingVitals.length === 0) return;

    console.log('[SW] Syncing vitals:', pendingVitals.length);

    for (const vital of pendingVitals) {
      const formData = new URLSearchParams();
      for (const [key, value] of Object.entries(vital)) {
        formData.append(key, value);
      }

      await fetch('/new_vital_record', {
        method: 'POST',
        body: formData,
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
    }
    await clearPendingData('pending_vitals');
    console.log('[SW] Vitals synced successfully');
  } catch (error) {
    console.error('[SW] Sync vitals failed:', error);
  }
}

// Sync symptoms data when back online  
async function syncSymptomsData() {
  try {
    const pendingSymptoms = await getPendingData('pending_symptoms');
    if (!pendingSymptoms || pendingSymptoms.length === 0) return;

    for (const symptom of pendingSymptoms) {
      // If image is present (File or base64), we should use FormData
      // app.js saves 'symptom_image' (File) or 'camera_image' (base64 string)

      if (symptom.symptom_image || symptom.camera_image) {
        const formData = new FormData();
        formData.append('symptoms', symptom.symptom_description);
        formData.append('affected_area', symptom.affected_area);
        formData.append('severity', symptom.severity);
        formData.append('duration', symptom.duration);

        if (symptom.symptom_image) {
          formData.append('symptom_image', symptom.symptom_image);
        }
        if (symptom.camera_image) {
          formData.append('camera_image', symptom.camera_image);
        }

        await fetch('/new_symptom_report', {
          method: 'POST',
          body: formData
        });
      } else {
        // Text only fallback
        const formData = new URLSearchParams();
        formData.append('symptoms', symptom.symptom_description);
        formData.append('affected_area', symptom.affected_area);
        formData.append('severity', symptom.severity);
        formData.append('duration', symptom.duration);

        await fetch('/new_symptom_report', {
          method: 'POST',
          body: formData,
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
      }
    }
    await clearPendingData('pending_symptoms');
  } catch (error) {
    console.error('[SW] Sync symptoms failed:', error);
  }
}

// Sync prescriptions
async function syncPrescriptionsData() {
  try {
    const pendingPrescriptions = await getPendingData('pending_prescriptions');
    if (!pendingPrescriptions || pendingPrescriptions.length === 0) return;

    for (const prescription of pendingPrescriptions) {
      const formData = new FormData();

      if (prescription.prescription_image) {
        formData.append('prescription_image', prescription.prescription_image);
      }
      if (prescription.camera_image) {
        formData.append('camera_image', prescription.camera_image);
      }

      formData.append('language', prescription.language);

      await fetch('/new_prescription', {
        method: 'POST',
        body: formData
      });
    }
    await clearPendingData('pending_prescriptions');
  } catch (error) {
    console.error('[SW] Sync prescriptions failed:', error);
  }
}

// Helper: Open IDB
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('telemedicine-db', 2);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    // On upgrade is handled in app.js, SW assumes DB logic matches
  });
}

// Helper to get pending data from IndexedDB
async function getPendingData(storeName) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readonly');
    const store = transaction.objectStore(storeName);
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function clearPendingData(storeName) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readwrite');
    const store = transaction.objectStore(storeName);
    const request = store.clear();
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
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
