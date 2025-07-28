// Additional JavaScript functionality for the Tesseract OCR Web Interface

// Utility functions
const utils = {
    // Format file size
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    // Validate image file type
    isValidImageFile(file) {
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff', 'image/gif'];
        return validTypes.includes(file.type);
    },

    // Format timestamp
    formatTimestamp(date = new Date()) {
        return date.toLocaleString();
    },

    // Debounce function for search inputs
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Enhanced file validation
function validateFile(file) {
    if (!utils.isValidImageFile(file)) {
        addMessage(`Invalid file type: ${file.type}. Please select an image file.`, 'error');
        return false;
    }
    
    if (file.size > 50 * 1024 * 1024) { // 50MB limit
        addMessage(`File too large: ${utils.formatFileSize(file.size)}. Maximum size is 50MB.`, 'error');
        return false;
    }
    
    return true;
}

// Enhanced keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+Enter to process OCR
    if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        processOCR();
    }
    
    // Escape to clear output
    if (e.key === 'Escape') {
        e.preventDefault();
        clearOutput();
    }
});

// Auto-save form data to localStorage
function saveFormData() {
    const formData = {
        imagePath: document.getElementById('imagePath').value,
        outputFolder: document.getElementById('outputFolder').value,
        batchFolder: document.getElementById('batchFolder').value,
        batchOutputFolder: document.getElementById('batchOutputFolder').value,
        txtFilePath: document.getElementById('txtFilePath').value,
        queryWord: document.getElementById('queryWord').value,
        wordLimit: document.getElementById('wordLimit').value,
        jsonFolder: document.getElementById('jsonFolder').value,
        bibQuery: document.getElementById('bibQuery').value,
        authorName: document.getElementById('authorName').value,
        bibLimit: document.getElementById('bibLimit').value,
        startYear: document.getElementById('startYear').value,
        endYear: document.getElementById('endYear').value,
        displayFormat: document.getElementById('displayFormat').value
    };
    
    localStorage.setItem('tesseractFormData', JSON.stringify(formData));
}

// Load form data from localStorage
function loadFormData() {
    const savedData = localStorage.getItem('tesseractFormData');
    if (savedData) {
        try {
            const formData = JSON.parse(savedData);
            Object.keys(formData).forEach(key => {
                const element = document.getElementById(key);
                if (element && formData[key]) {
                    element.value = formData[key];
                }
            });
        } catch (e) {
            console.warn('Failed to load saved form data:', e);
        }
    }
}

// Enhanced initialization
document.addEventListener('DOMContentLoaded', function() {
    // Load saved form data
    loadFormData();
    
    // Auto-save form data on input changes
    const formElements = document.querySelectorAll('input, select');
    formElements.forEach(element => {
        element.addEventListener('input', utils.debounce(saveFormData, 500));
    });
    
    // Add tooltips (simple implementation)
    const tooltips = {
        'imagePath': 'Path to the image file you want to process with OCR',
        'outputFolder': 'Folder where the text transcription will be saved',
        'batchFolder': 'Folder containing multiple images to process',
        'txtFilePath': 'Path to a text file for word frequency analysis',
        'queryWord': 'Specific word to search for in the frequency database',
        'jsonFolder': 'Folder containing JSON bibliography files',
        'bibQuery': 'Search terms for bibliography entries',
        'authorName': 'Author name to search for in bibliography',
        'startYear': 'Beginning year for publication date range',
        'endYear': 'End year for publication date range'
    };
    
    Object.keys(tooltips).forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.title = tooltips[id];
        }
    });
    
    console.log('Tesseract OCR Web Interface initialized');
}); 