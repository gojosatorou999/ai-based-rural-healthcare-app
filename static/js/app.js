// Rural Telemedicine Platform - Main JavaScript
// PWA functionality, offline support, and UI interactions

class TelemedicineApp {
    constructor() {
        this.db = null;
        this.isOnline = navigator.onLine;
        this.init();
    }

    async init() {
        // Register service worker
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/static/sw.js');
                console.log('ServiceWorker registered:', registration.scope);

                // Check for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showUpdateNotification();
                        }
                    });
                });
            } catch (error) {
                console.error('ServiceWorker registration failed:', error);
            }
        }

        // Initialize IndexedDB
        await this.initDB();

        // Setup online/offline handlers
        this.setupNetworkHandlers();

        // Setup form handlers
        this.setupFormHandlers();

        // Request notification permission
        this.requestNotificationPermission();

        // Setup install prompt
        this.setupInstallPrompt();
    }

    async initDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('TelemedicineDB', 1);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Create object stores
                if (!db.objectStoreNames.contains('pending_symptoms')) {
                    db.createObjectStore('pending_symptoms', { keyPath: 'id', autoIncrement: true });
                }

                if (!db.objectStoreNames.contains('pending_vitals')) {
                    db.createObjectStore('pending_vitals', { keyPath: 'id', autoIncrement: true });
                }

                if (!db.objectStoreNames.contains('pending_prescriptions')) {
                    db.createObjectStore('pending_prescriptions', { keyPath: 'id', autoIncrement: true });
                }

                if (!db.objectStoreNames.contains('offline_data')) {
                    const store = db.createObjectStore('offline_data', { keyPath: 'key' });
                    store.createIndex('timestamp', 'timestamp', { unique: false });
                }

                if (!db.objectStoreNames.contains('cached_recommendations')) {
                    db.createObjectStore('cached_recommendations', { keyPath: 'id', autoIncrement: true });
                }
            };
        });
    }

    setupNetworkHandlers() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.showNotification('Back Online', 'Connection restored. Syncing data...', 'success');
            this.syncPendingData();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.showNotification('Offline Mode', 'You are offline. Data will be synced when connection is restored.', 'warning');
        });

        // Update online status indicator
        this.updateOnlineStatus();
    }

    updateOnlineStatus() {
        const indicator = document.getElementById('online-status');
        if (indicator) {
            indicator.className = this.isOnline ? 'online' : 'offline';
            indicator.textContent = this.isOnline ? 'Online' : 'Offline';
        }
    }

    setupFormHandlers() {
        // Handle symptom form submission
        const symptomForm = document.getElementById('symptomForm');
        if (symptomForm) {
            symptomForm.addEventListener('submit', (e) => this.handleSymptomSubmit(e));
        }

        // Handle vitals form submission
        const vitalsForm = document.getElementById('vitalsForm');
        if (vitalsForm) {
            vitalsForm.addEventListener('submit', (e) => this.handleVitalsSubmit(e));
        }

        // Handle prescription form submission
        const prescriptionForm = document.getElementById('prescriptionForm');
        if (prescriptionForm) {
            prescriptionForm.addEventListener('submit', (e) => this.handlePrescriptionSubmit(e));
        }
    }

    async handleSymptomSubmit(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);

        if (!this.isOnline) {
            // Save to IndexedDB for later sync
            await this.saveSymptomOffline(formData);
            this.showNotification('Saved Offline', 'Symptom report will be submitted when online', 'info');
            return;
        }

        // Submit online
        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                window.location.href = data.redirect;
            } else {
                this.showNotification('Error', data.error || 'Failed to submit', 'error');
            }
        } catch (error) {
            // Save offline if network error
            await this.saveSymptomOffline(formData);
            this.showNotification('Saved Offline', 'Will sync when connection is restored', 'warning');
        }
    }

    async handleVitalsSubmit(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);

        if (!this.isOnline) {
            await this.saveVitalsOffline(formData);
            this.showNotification('Saved Offline', 'Vitals will be submitted when online', 'info');
            return;
        }

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                if (data.analysis && data.analysis.alerts) {
                    this.showNotification('Health Alert', data.analysis.alerts.join(', '), 'warning');
                }
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 2000);
            } else {
                this.showNotification('Error', data.error || 'Failed to submit', 'error');
            }
        } catch (error) {
            await this.saveVitalsOffline(formData);
            this.showNotification('Saved Offline', 'Will sync when connection is restored', 'warning');
        }
    }

    async handlePrescriptionSubmit(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);

        if (!this.isOnline) {
            await this.savePrescriptionOffline(formData);
            this.showNotification('Saved Offline', 'Prescription will be processed when online', 'info');
            return;
        }

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                window.location.href = data.redirect;
            } else {
                this.showNotification('Error', data.error || 'Failed to process', 'error');
            }
        } catch (error) {
            await this.savePrescriptionOffline(formData);
            this.showNotification('Saved Offline', 'Will sync when connection is restored', 'warning');
        }
    }

    async saveSymptomOffline(formData) {
        const data = {
            symptom_description: formData.get('symptom_description'),
            affected_area: formData.get('affected_area'),
            severity: formData.get('severity'),
            duration: formData.get('duration'),
            timestamp: new Date().toISOString()
        };

        const tx = this.db.transaction('pending_symptoms', 'readwrite');
        await tx.objectStore('pending_symptoms').add(data);

        // Register background sync
        if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
            const registration = await navigator.serviceWorker.ready;
            await registration.sync.register('sync-symptoms');
        }
    }

    async saveVitalsOffline(formData) {
        const data = {
            bp_systolic: formData.get('bp_systolic'),
            bp_diastolic: formData.get('bp_diastolic'),
            glucose: formData.get('glucose'),
            temperature: formData.get('temperature'),
            weight: formData.get('weight'),
            heart_rate: formData.get('heart_rate'),
            oxygen_saturation: formData.get('oxygen_saturation'),
            notes: formData.get('notes'),
            timestamp: new Date().toISOString()
        };

        const tx = this.db.transaction('pending_vitals', 'readwrite');
        await tx.objectStore('pending_vitals').add(data);

        if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
            const registration = await navigator.serviceWorker.ready;
            await registration.sync.register('sync-vitals');
        }
    }

    async savePrescriptionOffline(formData) {
        const data = {
            image: formData.get('prescription_image'),
            language: formData.get('language'),
            timestamp: new Date().toISOString()
        };

        const tx = this.db.transaction('pending_prescriptions', 'readwrite');
        await tx.objectStore('pending_prescriptions').add(data);

        if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
            const registration = await navigator.serviceWorker.ready;
            await registration.sync.register('sync-prescriptions');
        }
    }

    async syncPendingData() {
        // Trigger background sync for all pending data
        if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
            const registration = await navigator.serviceWorker.ready;
            await registration.sync.register('sync-symptoms');
            await registration.sync.register('sync-vitals');
            await registration.sync.register('sync-prescriptions');
        }
    }

    async requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            const permission = await Notification.requestPermission();
            console.log('Notification permission:', permission);
        }
    }

    setupInstallPrompt() {
        let deferredPrompt;

        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;

            // Show install button
            const installBtn = document.getElementById('install-btn');
            if (installBtn) {
                installBtn.style.display = 'block';
                installBtn.addEventListener('click', async () => {
                    deferredPrompt.prompt();
                    const { outcome } = await deferredPrompt.userChoice;
                    console.log('Install prompt outcome:', outcome);
                    deferredPrompt = null;
                    installBtn.style.display = 'none';
                });
            }
        });

        window.addEventListener('appinstalled', () => {
            console.log('PWA installed');
            this.showNotification('App Installed', 'Telemedicine app is now installed!', 'success');
        });
    }

    showNotification(title, message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} slide-down`;
        notification.innerHTML = `
      <i class="fas fa-${this.getIconForType(type)}"></i>
      <div>
        <strong>${title}</strong>
        <p style="margin: 0;">${message}</p>
      </div>
    `;

        // Add to page
        const container = document.getElementById('notification-container') || document.body;
        container.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }

    showUpdateNotification() {
        const updateBanner = document.createElement('div');
        updateBanner.className = 'update-banner';
        updateBanner.innerHTML = `
      <p>A new version is available!</p>
      <button class="btn btn-sm btn-primary" onclick="window.location.reload()">Update Now</button>
    `;
        document.body.prepend(updateBanner);
    }

    getIconForType(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.telemedicineApp = new TelemedicineApp();
    });
} else {
    window.telemedicineApp = new TelemedicineApp();
}

// Utility functions
function showLoading(message = 'Loading...') {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.innerHTML = `
    <div class="loading-content">
      <div class="spinner"></div>
      <p>${message}</p>
    </div>
  `;
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Image compression for uploads
async function compressImage(file, maxWidth = 800, quality = 0.6) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas');
                let width = img.width;
                let height = img.height;

                if (width > maxWidth) {
                    height = (height * maxWidth) / width;
                    width = maxWidth;
                }

                canvas.width = width;
                canvas.height = height;

                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);

                canvas.toBlob((blob) => {
                    resolve(new File([blob], file.name, {
                        type: 'image/webp',
                        lastModified: Date.now()
                    }));
                }, 'image/webp', quality);
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });
}

// Export for use in other scripts
window.telemedicineUtils = {
    showLoading,
    hideLoading,
    compressImage
};
