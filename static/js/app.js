// Rural Telemedicine Platform - Main JavaScript
// PWA functionality, offline support, and UI interactions

class TelemedicineApp {
    constructor() {
        this.db = null;
        this.isOnline = navigator.onLine;
        this.init();
    }

    async init() {
        console.log('Initializing Telemedicine App...');

        try {
            // 1. Initialize Essential Data Stores
            await this.initDB();

            // 2. Setup Core Handlers
            this.setupNetworkHandlers();
            this.setupFormHandlers();
            this.setupInstallPrompt();

            // 3. Register Service Worker (Non-blocking)
            if ('serviceWorker' in navigator) {
                this.registerServiceWorker();
            }

            // 4. Other features
            this.requestNotificationPermission();
            this.setupIOSPrompt();
            this.startKeepAlive();

            console.log('App initialized successfully.');
        } catch (error) {
            console.error('Critical initialization error:', error);
        }
    }

    async registerServiceWorker() {
        try {
            const registration = await navigator.serviceWorker.register('/sw.js');
            console.log('ServiceWorker registered:', registration.scope);

            registration.addEventListener('updatefound', () => {
                const newWorker = registration.installing;
                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        this.showUpdateNotification();
                    }
                });
            });
        } catch (error) {
            console.warn('ServiceWorker registration failed:', error);
        }
    }

    async initDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('PristinHealthDB', 1);

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
        // Read file if present
        let symptomImage = formData.get('symptom_image');
        // If it's a file, we can store it directly in IDB (Blob/File support)

        const data = {
            symptom_description: formData.get('symptom_description') || formData.get('symptoms'), // handle field name variation
            affected_area: formData.get('affected_area'),
            severity: formData.get('severity'),
            duration: formData.get('duration'),
            camera_image: formData.get('camera_image'),
            symptom_image: symptomImage instanceof File && symptomImage.size > 0 ? symptomImage : null,
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
        let prescriptionImage = formData.get('prescription_image');

        const data = {
            prescription_image: prescriptionImage instanceof File && prescriptionImage.size > 0 ? prescriptionImage : null,
            camera_image: formData.get('camera_image'),
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

    setupIOSPrompt() {
        // Detect if device is iOS
        const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
        const isStandalone = window.navigator.standalone === true || window.matchMedia('(display-mode: standalone)').matches;

        if (isIOS && !isStandalone) {
            this.injectIOSPrompt();
        }
    }

    injectIOSPrompt() {
        if (document.querySelector('.ios-install-prompt')) return;

        const prompt = document.createElement('div');
        prompt.className = 'ios-install-prompt';
        prompt.innerHTML = `
            <div class="ios-install-icon">
                <i class="fas fa-heartbeat"></i>
            </div>
            <div class="ios-install-title">Install Pristin Healthcare</div>
            <div class="ios-install-text">Install this app on your iPhone for the best experience and offline access.</div>
            <div class="ios-install-steps">
                <div class="ios-install-step">
                    <div class="ios-step-icon"><i class="fas fa-share-square"></i></div>
                    <span>Tap the <strong>Share</strong> button in the bottom bar.</span>
                </div>
                <div class="ios-install-step">
                    <div class="ios-step-icon"><i class="fas fa-plus-square"></i></div>
                    <span>Scroll down and tap <strong>Add to Home Screen</strong>.</span>
                </div>
            </div>
            <div class="ios-install-close" onclick="this.parentElement.classList.remove('active')">Not now</div>
        `;

        document.body.appendChild(prompt);

        // Show after 3 seconds
        setTimeout(() => {
            prompt.classList.add('active');
        }, 3000);
    }

    setupInstallPrompt() {
        let deferredPrompt;

        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;

            // Show install button (Header ID updated)
            const installBtn = document.getElementById('installApp') || document.getElementById('installBtn');
            const installPrompt = document.getElementById('installPrompt');

            if (installPrompt) installPrompt.style.display = 'block';

            if (installBtn) {
                installBtn.style.display = 'flex'; // Use flex for icon alignment
                installBtn.addEventListener('click', async () => {
                    deferredPrompt.prompt();
                    const { outcome } = await deferredPrompt.userChoice;
                    console.log('Install prompt outcome:', outcome);
                    deferredPrompt = null;
                    if (installPrompt) installPrompt.style.display = 'none';
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
    startKeepAlive() {
        setInterval(async () => {
            if (this.isOnline) {
                try {
                    await fetch('/robots.txt', { method: 'HEAD', cache: 'no-store' });
                } catch (e) {
                    console.warn('Keep-alive ping failed:', e);
                }
            }
        }, 15000); // Every 15 seconds
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

// --- Theme Management ---
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';

    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = document.querySelector('.theme-toggle i');
    if (icon) {
        if (theme === 'light') {
            icon.className = 'fas fa-sun';
        } else {
            icon.className = 'fas fa-moon';
        }
    }
}

// Initialize Theme
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
});




// --- Chatbot Functionality ---
function toggleChat() {
    const chatWindow = document.getElementById('chatWindow');
    if (chatWindow) {
        chatWindow.classList.toggle('active');
        if (chatWindow.classList.contains('active')) {
            const input = document.getElementById('chatInput');
            if (input) setTimeout(() => input.focus(), 300); // Wait for animation
        }
    }
}

function handleChatEnter(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    if (!input) return;

    const message = input.value.trim();
    const messagesContainer = document.getElementById('chatMessages');

    if (!message) return;

    // Add user message
    appendMessage(message, 'user');
    input.value = '';

    // Show typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.innerHTML = '<i class="fas fa-circle-notch fa-spin text-primary"></i> <span class="text-xs text-muted">Pristin AI is thinking...</span>';
    typingDiv.style.padding = '0.5rem';
    typingDiv.style.display = 'flex';
    typingDiv.style.gap = '0.5rem';
    typingDiv.style.alignItems = 'center';

    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        // Remove typing indicator
        typingDiv.remove();

        if (data.response) {
            appendMessage(data.response, 'bot');
        } else if (data.error) {
            appendMessage("Error: " + data.error, 'bot');
        }
    } catch (error) {
        if (typingDiv) typingDiv.remove();
        appendMessage("Network error. Please try again.", 'bot');
    }
}

function appendMessage(text, sender) {
    const container = document.getElementById('chatMessages');
    if (!container) return;

    const div = document.createElement('div');

    // Modern Chat Styling
    if (sender === 'user') {
        div.className = 'chat-bubble user-message';
        div.style.alignSelf = 'flex-end';
        div.style.background = 'var(--primary)';
        div.style.color = 'white';
        div.style.padding = '0.75rem 1rem';
        div.style.borderRadius = '1rem 1rem 0 1rem';
        div.style.maxWidth = '85%';
        div.style.marginBottom = '0.5rem';
        div.style.fontSize = '0.9rem';
        div.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';
    } else {
        div.className = 'chat-bubble bot-message';
        div.style.alignSelf = 'flex-start';
        div.style.background = 'rgba(255, 255, 255, 0.1)';
        div.style.backdropFilter = 'blur(4px)';
        div.style.border = '1px solid var(--border-color)';
        div.style.color = 'var(--text-primary)';
        div.style.padding = '0.75rem 1rem';
        div.style.borderRadius = '1rem 1rem 1rem 0';
        div.style.maxWidth = '85%';
        div.style.marginBottom = '0.5rem';
        div.style.fontSize = '0.9rem';
    }

    // Format simple markdown-like syntax
    let formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formattedText = formattedText.replace(/\n/g, '<br>');

    div.innerHTML = formattedText;
    container.appendChild(div);

    // Scroll to bottom
    requestAnimationFrame(() => {
        container.scrollTop = container.scrollHeight;
    });
}

// --- IoT Device Simulation ---
async function connectIoTDevice() {
    const statusText = document.getElementById('iotStatusText');
    const statusPulse = document.getElementById('iotStatusPulse');
    const connectBtn = document.getElementById('iotConnectBtn');

    if (!statusText) return;

    // Loading state
    statusText.innerText = "Searching for devices...";
    statusText.style.color = "var(--warning)";

    if (connectBtn) {
        connectBtn.disabled = true;
        connectBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Scanning...';

        try {
            const response = await fetch('/api/iot/connect', { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                statusText.innerText = `Connected: ${data.device_name} (Active)`;
                statusText.style.color = "var(--success)";

                if (statusPulse) {
                    statusPulse.style.background = "var(--success)";
                    statusPulse.style.boxShadow = "0 0 15px var(--success)";
                    statusPulse.style.animation = "pulse 2s infinite";
                }

                connectBtn.innerHTML = '<i class="fas fa-check"></i> Connected';
                connectBtn.style.color = 'var(--success)';
                connectBtn.style.borderColor = 'var(--success)';

                // Show success notification
                if (window.telemedicineApp) {
                    window.telemedicineApp.showNotification('Device Connected', data.message, 'success');
                }

                // Start fetching data from backend
                fetchIoTData();
            } else {
                throw new Error("Connection failed");
            }
        } catch (error) {
            console.error('IoT Connection Error:', error);
            statusText.innerText = "Connection Failed. Try again.";
            statusText.style.color = "var(--danger)";

            connectBtn.disabled = false;
            connectBtn.innerHTML = '<i class="fas fa-wifi"></i> Connect Device';

            if (window.telemedicineApp) {
                window.telemedicineApp.showNotification('Connection Error', 'Could not connect to medical device.', 'error');
            }
        }
    }
}

async function fetchIoTData() {
    try {
        const response = await fetch('/api/iot/data');
        if (!response.ok) throw new Error('Failed to fetch data');

        const inputs = await response.json();

        // Apply values to form fields with a cascading effect
        Object.keys(inputs).forEach((key, index) => {
            setTimeout(() => {
                const input = document.querySelector(`input[name="${key}"]`);
                if (input) {
                    input.value = inputs[key];

                    // Visual feedback
                    const originalBg = input.style.backgroundColor;
                    const originalBorder = input.style.borderColor;

                    input.style.borderColor = "var(--primary)";
                    input.style.backgroundColor = "rgba(59, 130, 246, 0.1)";
                    input.style.transition = "all 0.3s";

                    // Reset after highlight
                    setTimeout(() => {
                        input.style.backgroundColor = originalBg;
                        input.style.borderColor = originalBorder;
                    }, 1000);
                }
            }, index * 400);
        });
    } catch (error) {
        console.error('Error fetching IoT data:', error);
    }
}

// Theme Management
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    html.setAttribute('data-theme', newTheme);
    document.body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Update icons in all theme toggle buttons
    const themeIcons = document.querySelectorAll('.theme-toggle i');
    themeIcons.forEach(icon => {
        icon.className = newTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
    });
}

// Initial theme application
(function () {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    document.body.setAttribute('data-theme', savedTheme); // Ensure body also gets theme immediately

    // Update icons based on saved theme
    const themeIcons = document.querySelectorAll('.theme-toggle i');
    themeIcons.forEach(icon => {
        icon.className = savedTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
    });
})();
