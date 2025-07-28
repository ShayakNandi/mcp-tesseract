// Flask-SocketIO specific functionality

// Enhanced SocketIO connection management
class FlaskSocketManager {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
    }

    connect() {
        this.socket = io({
            transports: ['websocket', 'polling'],
            upgrade: true,
            timeout: 20000
        });

        this.socket.on('connect', () => {
            this.reconnectAttempts = 0;
            this.updateConnectionStatus(true);
            console.log('Flask-SocketIO connected');
        });

        this.socket.on('disconnect', (reason) => {
            this.updateConnectionStatus(false);
            console.log('Flask-SocketIO disconnected:', reason);
            
            if (reason === 'io server disconnect') {
                // Server initiated disconnect, manual reconnection required
                this.attemptReconnect();
            }
        });

        this.socket.on('connect_error', (error) => {
            console.error('Flask-SocketIO connection error:', error);
            this.attemptReconnect();
        });

        return this.socket;
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
                console.log(`Reconnection attempt ${this.reconnectAttempts}`);
                this.socket.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        }
    }

    updateConnectionStatus(connected) {
        const indicator = document.getElementById('connectionIndicator');
        if (!indicator) {
            // Create connection indicator
            const div = document.createElement('div');
            div.id = 'connectionIndicator';
            div.className = 'socketio-indicator';
            document.body.appendChild(div);
        }
        
        const statusEl = document.getElementById('connectionIndicator');
        if (connected) {
            statusEl.className = 'socketio-indicator connected';
            statusEl.textContent = '🔗 Flask Connected';
        } else {
            statusEl.className = 'socketio-indicator disconnected';
            statusEl.textContent = '❌ Disconnected';
        }
    }
}

// Enhanced file handling for Flask
const FlaskFileHandler = {
    validateFile(file) {
        const maxSize = 50 * 1024 * 1024; // 50MB
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff', 'image/gif'];
        
        if (!allowedTypes.includes(file.type)) {
            throw new Error(`Invalid file type: ${file.type}`);
        }
        
        if (file.size > maxSize) {
            throw new Error(`File too large: ${this.formatFileSize(file.size)}`);
        }
        
        return true;
    },

    formatFileSize(bytes) {
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 Bytes';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    },

    async uploadToFlask(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }
        
        return await response.json();
    }
};

// Flask-specific progress tracking
class FlaskProgressTracker {
    constructor() {
        this.activeOperations = new Set();
    }

    startOperation(operationId) {
        this.activeOperations.add(operationId);
        this.updateProgress();
    }

    endOperation(operationId) {
        this.activeOperations.delete(operationId);
        this.updateProgress();
    }

    updateProgress() {
        const progressBar = document.getElementById('progressBar');
        const progressFill = document.getElementById('progressFill');
        
        if (this.activeOperations.size > 0) {
            progressBar.style.display = 'block';
            progressFill.style.width = '100%';
            progressFill.classList.add('flask-processing');
        } else {
            setTimeout(() => {
                progressBar.style.display = 'none';
                progressFill.style.width = '0%';
                progressFill.classList.remove('flask-processing');
            }, 500);
        }
    }
}

// Initialize Flask-specific functionality
const flaskSocketManager = new FlaskSocketManager();
const flaskProgressTracker = new FlaskProgressTracker();

// Enhanced keyboard shortcuts for Flask
document.addEventListener('keydown', function(e) {
    // Alt + F for Flask-specific actions
    if (e.altKey && e.key === 'f') {
        e.preventDefault();
        console.log('Flask shortcut triggered');
        // Add custom Flask functionality here
    }
    
    // Ctrl + Shift + R to reconnect
    if (e.ctrlKey && e.shiftKey && e.key === 'R') {
        e.preventDefault();
        flaskSocketManager.socket?.disconnect();
        flaskSocketManager.connect();
    }
});

// Flask performance monitoring
const FlaskMonitor = {
    startTime: null,
    
    startOperation() {
        this.startTime = performance.now();
    },
    
    endOperation(operationName) {
        if (this.startTime) {
            const duration = performance.now() - this.startTime;
            console.log(`Flask operation '${operationName}' took ${duration.toFixed(2)}ms`);
            this.startTime = null;
        }
    }
};

// Auto-save specific to Flask
const FlaskAutoSave = {
    saveInterval: 5000, // 5 seconds
    
    init() {
        setInterval(() => {
            this.saveFormData();
        }, this.saveInterval);
    },
    
    saveFormData() {
        const formData = {
            timestamp: new Date().toISOString(),
            imagePath: document.getElementById('imagePath')?.value || '',
            outputFolder: document.getElementById('outputFolder')?.value || '',
            batchFolder: document.getElementById('batchFolder')?.value || '',
            txtFilePath: document.getElementById('txtFilePath')?.value || '',
            queryWord: document.getElementById('queryWord')?.value || ''
        };
        
        localStorage.setItem('flaskTesseractData', JSON.stringify(formData));
    },
    
    loadFormData() {
        try {
            const saved = localStorage.getItem('flaskTesseractData');
            if (saved) {
                const data = JSON.parse(saved);
                Object.keys(data).forEach(key => {
                    if (key !== 'timestamp') {
                        const element = document.getElementById(key);
                        if (element && data[key]) {
                            element.value = data[key];
                        }
                    }
                });
                console.log('Flask form data restored from:', data.timestamp);
            }
        } catch (e) {
            console.warn('Failed to load Flask form data:', e);
        }
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    FlaskAutoSave.init();
    FlaskAutoSave.loadFormData();
    console.log('Flask-specific functionality initialized');
}); 