/**
 * Pristin Healthcare - Offline Database
 * IndexedDB wrapper for offline patient data storage and sync
 */

const DB_NAME = 'PristinHealthDB';
const DB_VERSION = 1;

// Store names
const STORES = {
    VITALS: 'vitals',
    SYMPTOMS: 'symptoms',
    PRESCRIPTIONS: 'prescriptions',
    SYNC_QUEUE: 'sync-queue',
    DIAGNOSIS_LIBRARY: 'diagnosis-library'
};

class OfflineDB {
    constructor() {
        this.db = null;
        this.isOnline = navigator.onLine;
        this.setupConnectionListeners();
    }

    // Initialize the database
    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                console.log('[OfflineDB] Database initialized');
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Vitals store - for offline vital records
                if (!db.objectStoreNames.contains(STORES.VITALS)) {
                    const vitalsStore = db.createObjectStore(STORES.VITALS, {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    vitalsStore.createIndex('timestamp', 'timestamp', { unique: false });
                    vitalsStore.createIndex('synced', 'synced', { unique: false });
                }

                // Symptoms store - for offline symptom reports
                if (!db.objectStoreNames.contains(STORES.SYMPTOMS)) {
                    const symptomsStore = db.createObjectStore(STORES.SYMPTOMS, {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    symptomsStore.createIndex('timestamp', 'timestamp', { unique: false });
                    symptomsStore.createIndex('synced', 'synced', { unique: false });
                }

                // Prescriptions store - for cached prescriptions
                if (!db.objectStoreNames.contains(STORES.PRESCRIPTIONS)) {
                    const prescStore = db.createObjectStore(STORES.PRESCRIPTIONS, {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    prescStore.createIndex('timestamp', 'timestamp', { unique: false });
                }

                // Sync queue - for pending server syncs
                if (!db.objectStoreNames.contains(STORES.SYNC_QUEUE)) {
                    const syncStore = db.createObjectStore(STORES.SYNC_QUEUE, {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    syncStore.createIndex('type', 'type', { unique: false });
                    syncStore.createIndex('timestamp', 'timestamp', { unique: false });
                }

                // Diagnosis library - for offline diagnosis reference
                if (!db.objectStoreNames.contains(STORES.DIAGNOSIS_LIBRARY)) {
                    const diagStore = db.createObjectStore(STORES.DIAGNOSIS_LIBRARY, {
                        keyPath: 'id'
                    });
                    diagStore.createIndex('name', 'name', { unique: false });
                    diagStore.createIndex('category', 'category', { unique: false });
                }

                console.log('[OfflineDB] Database schema created');
            };
        });
    }

    // Setup online/offline listeners
    setupConnectionListeners() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            console.log('[OfflineDB] Connection restored');
            this.syncPendingData();
            this.updateConnectionStatus(true);
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            console.log('[OfflineDB] Connection lost');
            this.updateConnectionStatus(false);
        });
    }

    // Update UI connection status
    updateConnectionStatus(online) {
        const statusEl = document.querySelector('.connection-status');
        if (statusEl) {
            statusEl.classList.toggle('offline', !online);
            statusEl.innerHTML = online
                ? '<i class="fas fa-wifi"></i> Online'
                : '<i class="fas fa-wifi-slash"></i> Offline Mode';
        }

        // Show toast notification
        if (!online) {
            this.showToast('You are now offline. Data will sync when connection is restored.', 'warning');
        } else {
            this.showToast('Connection restored! Syncing data...', 'success');
        }
    }

    // Show toast notification
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        document.body.appendChild(toast);

        setTimeout(() => toast.classList.add('show'), 100);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // ========== VITALS OPERATIONS ==========

    async saveVitals(vitalsData) {
        const record = {
            ...vitalsData,
            timestamp: new Date().toISOString(),
            synced: this.isOnline
        };

        const id = await this.addToStore(STORES.VITALS, record);

        if (this.isOnline) {
            // Try to sync immediately
            try {
                await this.syncVitalsToServer(record);
                await this.markAsSynced(STORES.VITALS, id);
            } catch (error) {
                console.error('[OfflineDB] Failed to sync vitals:', error);
                await this.addToSyncQueue('vitals', id, record);
            }
        } else {
            await this.addToSyncQueue('vitals', id, record);
        }

        return id;
    }

    async getVitalsHistory(limit = 30) {
        return this.getAllFromStore(STORES.VITALS, limit);
    }

    // ========== SYMPTOMS OPERATIONS ==========

    async saveSymptoms(symptomData) {
        const record = {
            ...symptomData,
            timestamp: new Date().toISOString(),
            synced: this.isOnline
        };

        const id = await this.addToStore(STORES.SYMPTOMS, record);

        if (this.isOnline) {
            try {
                await this.syncSymptomsToServer(record);
                await this.markAsSynced(STORES.SYMPTOMS, id);
            } catch (error) {
                console.error('[OfflineDB] Failed to sync symptoms:', error);
                await this.addToSyncQueue('symptoms', id, record);
            }
        } else {
            await this.addToSyncQueue('symptoms', id, record);
        }

        return id;
    }

    async getSymptomsHistory(limit = 20) {
        return this.getAllFromStore(STORES.SYMPTOMS, limit);
    }

    // ========== SYNC OPERATIONS ==========

    async addToSyncQueue(type, recordId, data) {
        return this.addToStore(STORES.SYNC_QUEUE, {
            type,
            recordId,
            data,
            timestamp: new Date().toISOString(),
            attempts: 0
        });
    }

    async syncPendingData() {
        const pendingItems = await this.getAllFromStore(STORES.SYNC_QUEUE);
        console.log(`[OfflineDB] Syncing ${pendingItems.length} pending items`);

        for (const item of pendingItems) {
            try {
                if (item.type === 'vitals') {
                    await this.syncVitalsToServer(item.data);
                } else if (item.type === 'symptoms') {
                    await this.syncSymptomsToServer(item.data);
                }

                // Remove from queue and mark original as synced
                await this.deleteFromStore(STORES.SYNC_QUEUE, item.id);
                await this.markAsSynced(
                    item.type === 'vitals' ? STORES.VITALS : STORES.SYMPTOMS,
                    item.recordId
                );

                console.log(`[OfflineDB] Synced ${item.type} record`);
            } catch (error) {
                console.error(`[OfflineDB] Sync failed for ${item.type}:`, error);
                // Increment retry counter
                item.attempts++;
                if (item.attempts < 5) {
                    await this.updateInStore(STORES.SYNC_QUEUE, item);
                }
            }
        }
    }

    async syncVitalsToServer(data) {
        const formData = new URLSearchParams();
        formData.append('bp_systolic', data.bp_systolic || '');
        formData.append('bp_diastolic', data.bp_diastolic || '');
        formData.append('glucose', data.glucose || '');
        formData.append('temperature', data.temperature || '');
        formData.append('heart_rate', data.heart_rate || '');
        formData.append('oxygen', data.oxygen || '');
        formData.append('weight', data.weight || '');
        formData.append('notes', data.notes || '');

        const response = await fetch('/new_vital_record', {
            method: 'POST',
            body: formData,
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });

        if (!response.ok) throw new Error('Sync failed');
        return response;
    }

    async syncSymptomsToServer(data) {
        const formData = new URLSearchParams();
        formData.append('symptoms', data.symptoms || '');
        formData.append('affected_area', data.affected_area || '');
        formData.append('severity', data.severity || '5');
        formData.append('duration', data.duration || '');

        const response = await fetch('/new_symptom_report', {
            method: 'POST',
            body: formData,
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });

        if (!response.ok) throw new Error('Sync failed');
        return response;
    }

    // ========== DIAGNOSIS LIBRARY ==========

    async loadDiagnosisLibrary() {
        // Pre-populate offline diagnosis database
        const diseases = [
            {
                id: 'flu', name: 'Influenza (Flu)', category: 'respiratory',
                symptoms: ['fever', 'cough', 'body aches', 'fatigue'],
                treatment: 'Rest, hydration, paracetamol for fever',
                medicines: ['Paracetamol 500mg', 'ORS', 'Cetirizine']
            },
            {
                id: 'diabetes', name: 'Type 2 Diabetes', category: 'metabolic',
                symptoms: ['increased thirst', 'frequent urination', 'fatigue', 'blurred vision'],
                treatment: 'Diet control, exercise, medication as prescribed',
                medicines: ['Metformin 500mg', 'Glucose monitor']
            },
            {
                id: 'hypertension', name: 'Hypertension', category: 'cardiovascular',
                symptoms: ['headache', 'dizziness', 'chest pain'],
                treatment: 'Low salt diet, exercise, medication',
                medicines: ['Amlodipine 5mg', 'BP monitor']
            },
            {
                id: 'gastritis', name: 'Gastritis', category: 'digestive',
                symptoms: ['stomach pain', 'nausea', 'bloating', 'loss of appetite'],
                treatment: 'Avoid spicy food, eat smaller meals, antacids',
                medicines: ['Pantoprazole 40mg', 'Antacid gel']
            },
            {
                id: 'malaria', name: 'Malaria', category: 'infectious',
                symptoms: ['high fever', 'chills', 'sweating', 'headache'],
                treatment: 'Antimalarial medication, rest, hydration',
                medicines: ['Chloroquine', 'Paracetamol', 'ORS']
            }
        ];

        for (const disease of diseases) {
            await this.addToStore(STORES.DIAGNOSIS_LIBRARY, disease);
        }
        console.log('[OfflineDB] Diagnosis library loaded');
    }

    async searchDiagnosis(query) {
        const all = await this.getAllFromStore(STORES.DIAGNOSIS_LIBRARY);
        const lowerQuery = query.toLowerCase();
        return all.filter(d =>
            d.name.toLowerCase().includes(lowerQuery) ||
            d.symptoms.some(s => s.includes(lowerQuery))
        );
    }

    // ========== GENERIC STORE OPERATIONS ==========

    addToStore(storeName, data) {
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(storeName, 'readwrite');
            const store = tx.objectStore(storeName);
            const request = store.add(data);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    getAllFromStore(storeName, limit = 100) {
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(storeName, 'readonly');
            const store = tx.objectStore(storeName);
            const request = store.getAll();
            request.onsuccess = () => {
                let results = request.result;
                // Sort by timestamp descending and limit
                results.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
                resolve(results.slice(0, limit));
            };
            request.onerror = () => reject(request.error);
        });
    }

    deleteFromStore(storeName, id) {
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(storeName, 'readwrite');
            const store = tx.objectStore(storeName);
            const request = store.delete(id);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    updateInStore(storeName, data) {
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(storeName, 'readwrite');
            const store = tx.objectStore(storeName);
            const request = store.put(data);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    markAsSynced(storeName, id) {
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(storeName, 'readwrite');
            const store = tx.objectStore(storeName);
            const getRequest = store.get(id);
            getRequest.onsuccess = () => {
                const record = getRequest.result;
                if (record) {
                    record.synced = true;
                    store.put(record);
                }
                resolve();
            };
            getRequest.onerror = () => reject(getRequest.error);
        });
    }

    // Get sync status
    async getSyncStatus() {
        const queue = await this.getAllFromStore(STORES.SYNC_QUEUE);
        return {
            pendingItems: queue.length,
            isOnline: this.isOnline,
            lastSync: localStorage.getItem('lastSyncTime') || 'Never'
        };
    }
}

// Initialize and export
const offlineDB = new OfflineDB();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await offlineDB.init();
        await offlineDB.loadDiagnosisLibrary();
        console.log('[OfflineDB] Ready for offline operations');
    } catch (error) {
        console.error('[OfflineDB] Initialization failed:', error);
    }
});

// Export for use in other scripts
window.OfflineDB = offlineDB;
