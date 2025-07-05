/**
 * Modern Medical PDF OCR Dashboard JavaScript
 * Handles file uploads, processing, and dashboard interactions
 */

class PDFDashboard {
    constructor() {
        this.apiBase = '';
        this.uploadQueue = [];
        this.results = [];
        this.stats = {
            total: 0,
            successful: 0,
            failed: 0,
            processing: 0
        };
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkSystemStatus();
        this.loadResults();
        this.updateStats();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchSection(item.dataset.section);
            });
        });

        // File upload
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');
        const uploadBtn = document.getElementById('upload-btn');

        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', this.handleDragOver.bind(this));
        dropZone.addEventListener('drop', this.handleFileDrop.bind(this));
        dropZone.addEventListener('dragleave', this.handleDragLeave.bind(this));

        fileInput.addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files);
        });

        uploadBtn.addEventListener('click', () => fileInput.click());

        // Table actions
        document.getElementById('clear-queue')?.addEventListener('click', this.clearQueue.bind(this));
        document.getElementById('process-all')?.addEventListener('click', this.processAll.bind(this));
        document.getElementById('download-all')?.addEventListener('click', this.downloadAll.bind(this));

        // Search functionality
        document.getElementById('search-input')?.addEventListener('input', this.handleSearch.bind(this));
    }

    switchSection(sectionId) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionId}"]`).classList.add('active');

        // Show/hide sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(`${sectionId}-section`).classList.add('active');

        // Update page title
        this.updatePageTitle(sectionId);
    }

    updatePageTitle(sectionId) {
        const titles = {
            dashboard: 'Assign PDFs To The Processing Queue',
            upload: 'Upload PDF Files',
            processing: 'Processing Status',
            results: 'Processing Results',
            analytics: 'Processing Analytics',
            history: 'Processing History'
        };

        const titleElement = document.querySelector('.page-title');
        if (titleElement && titles[sectionId]) {
            titleElement.textContent = titles[sectionId];
        }
    }

    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
        document.getElementById('drop-zone').classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        document.getElementById('drop-zone').classList.remove('dragover');
    }

    handleFileDrop(e) {
        e.preventDefault();
        document.getElementById('drop-zone').classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files).filter(file => 
            file.type === 'application/pdf'
        );
        
        if (files.length === 0) {
            this.showNotification('Please drop PDF files only', 'warning');
            return;
        }

        this.handleFileSelect(files);
    }

    handleFileSelect(files) {
        const pdfFiles = Array.from(files).filter(file => file.type === 'application/pdf');
        
        if (pdfFiles.length === 0) {
            this.showNotification('Please select PDF files only', 'warning');
            return;
        }

        if (pdfFiles.length !== files.length) {
            this.showNotification(`${files.length - pdfFiles.length} non-PDF files ignored`, 'warning');
        }

        // Add files to queue
        pdfFiles.forEach(file => {
            const fileObj = {
                id: Date.now() + Math.random(),
                file: file,
                name: file.name,
                size: file.size,
                status: 'pending',
                progress: 0,
                result: null
            };
            this.uploadQueue.push(fileObj);
        });

        this.updateTable();
        this.showNotification(`${pdfFiles.length} file(s) added to queue`, 'success');
    }

    updateTable() {
        const tbody = document.getElementById('files-table-body');
        
        if (this.uploadQueue.length === 0) {
            tbody.innerHTML = `
                <tr class="empty-state">
                    <td colspan="5">
                        <div class="empty-message">
                            <i class="fas fa-file-pdf"></i>
                            <p>No files in queue. Upload PDF files to get started.</p>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = this.uploadQueue.map(file => `
            <tr>
                <td>
                    <div class="file-info">
                        <i class="fas fa-file-pdf"></i>
                        <span class="file-name">${file.name}</span>
                    </div>
                </td>
                <td>${this.formatFileSize(file.size)}</td>
                <td>
                    <span class="status-badge ${file.status}">
                        ${file.status === 'processing' ? '<i class="fas fa-spinner fa-spin"></i>' : ''}
                        ${file.status.charAt(0).toUpperCase() + file.status.slice(1)}
                    </span>
                </td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${file.progress}%"></div>
                    </div>
                    <span class="progress-text">${file.progress}%</span>
                </td>
                <td>
                    <div class="file-actions">
                        ${file.status === 'pending' ? `
                            <button class="btn btn-sm btn-primary" onclick="dashboard.processFile('${file.id}')">
                                <i class="fas fa-play"></i> Process
                            </button>
                            <button class="btn btn-sm btn-secondary" onclick="dashboard.removeFile('${file.id}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : ''}
                        ${file.status === 'completed' ? `
                            <button class="btn btn-sm btn-success" onclick="dashboard.downloadResult('${file.id}')">
                                <i class="fas fa-download"></i> Download
                            </button>
                        ` : ''}
                        ${file.status === 'failed' ? `
                            <button class="btn btn-sm btn-warning" onclick="dashboard.retryFile('${file.id}')">
                                <i class="fas fa-redo"></i> Retry
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `).join('');
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async processFile(fileId) {
        const file = this.uploadQueue.find(f => f.id === fileId);
        if (!file) return;

        file.status = 'processing';
        file.progress = 0;
        this.updateTable();
        this.updateStats();

        const formData = new FormData();
        formData.append('file', file.file);
        formData.append('use_ocr', document.getElementById('use-ocr').checked);

        try {
            // Show loading
            this.showLoading(true);

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                file.status = 'completed';
                file.progress = 100;
                file.result = result.result;
                this.showNotification(`Successfully processed ${file.name}`, 'success');
                this.addToResults(file);
            } else {
                file.status = 'failed';
                file.progress = 0;
                file.error = result.error;
                this.showNotification(`Failed to process ${file.name}: ${result.error}`, 'error');
            }

        } catch (error) {
            file.status = 'failed';
            file.progress = 0;
            file.error = error.message;
            this.showNotification(`Error processing ${file.name}: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
            this.updateTable();
            this.updateStats();
        }
    }

    async processAll() {
        const pendingFiles = this.uploadQueue.filter(f => f.status === 'pending');
        
        if (pendingFiles.length === 0) {
            this.showNotification('No files to process', 'warning');
            return;
        }

        this.showLoading(true);

        const formData = new FormData();
        pendingFiles.forEach(file => {
            formData.append('files', file.file);
        });
        formData.append('use_ocr', document.getElementById('use-ocr').checked);

        // Update status for all files
        pendingFiles.forEach(file => {
            file.status = 'processing';
            file.progress = 0;
        });
        this.updateTable();
        this.updateStats();

        try {
            const response = await fetch('/api/batch-upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                // Update file statuses based on results
                result.results.forEach((processResult, index) => {
                    const file = pendingFiles[index];
                    if (file && processResult.success) {
                        file.status = 'completed';
                        file.progress = 100;
                        file.result = processResult;
                        this.addToResults(file);
                    } else if (file) {
                        file.status = 'failed';
                        file.progress = 0;
                        file.error = processResult.error;
                    }
                });

                this.showNotification(result.message, 'success');
            } else {
                pendingFiles.forEach(file => {
                    file.status = 'failed';
                    file.progress = 0;
                });
                this.showNotification(`Batch processing failed: ${result.error}`, 'error');
            }

        } catch (error) {
            pendingFiles.forEach(file => {
                file.status = 'failed';
                file.progress = 0;
                file.error = error.message;
            });
            this.showNotification(`Batch processing error: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
            this.updateTable();
            this.updateStats();
        }
    }

    removeFile(fileId) {
        this.uploadQueue = this.uploadQueue.filter(f => f.id !== fileId);
        this.updateTable();
        this.updateStats();
    }

    retryFile(fileId) {
        const file = this.uploadQueue.find(f => f.id === fileId);
        if (file) {
            file.status = 'pending';
            file.progress = 0;
            file.error = null;
            this.updateTable();
            this.updateStats();
        }
    }

    clearQueue() {
        this.uploadQueue = [];
        this.updateTable();
        this.updateStats();
        this.showNotification('Queue cleared', 'success');
    }

    addToResults(file) {
        this.results.unshift({
            id: file.id,
            name: file.name,
            size: file.size,
            timestamp: new Date().toISOString(),
            result: file.result
        });
        this.updateResultsList();
    }

    updateResultsList() {
        const resultsList = document.getElementById('results-list');
        
        if (this.results.length === 0) {
            resultsList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file-alt"></i>
                    <p>No processed files yet. Process some PDFs to see results here.</p>
                </div>
            `;
            return;
        }

        resultsList.innerHTML = this.results.slice(0, 10).map(result => `
            <div class="result-item">
                <div class="result-info">
                    <div class="result-icon">
                        <i class="fas fa-file-alt"></i>
                    </div>
                    <div class="result-details">
                        <div class="result-name">${result.name}</div>
                        <div class="result-meta">
                            ${this.formatFileSize(result.size)} • 
                            ${new Date(result.timestamp).toLocaleString()}
                        </div>
                    </div>
                </div>
                <div class="result-actions">
                    <button class="btn btn-sm btn-primary" onclick="dashboard.downloadResult('${result.id}')">
                        <i class="fas fa-download"></i> Download
                    </button>
                </div>
            </div>
        `).join('');
    }

    updateStats() {
        const stats = {
            total: this.uploadQueue.length,
            successful: this.uploadQueue.filter(f => f.status === 'completed').length,
            failed: this.uploadQueue.filter(f => f.status === 'failed').length,
            processing: this.uploadQueue.filter(f => f.status === 'processing').length
        };

        document.getElementById('total-files').textContent = stats.total;
        document.getElementById('successful-files').textContent = stats.successful;
        document.getElementById('failed-files').textContent = stats.failed;
        document.getElementById('processing-files').textContent = stats.processing;
    }

    async downloadResult(fileId) {
        const file = this.uploadQueue.find(f => f.id === fileId) || 
                    this.results.find(r => r.id === fileId);
        
        if (!file) {
            this.showNotification('File not found in queue or results', 'warning');
            return;
        }

        // If file has a result with output_filename, use that
        let filename = null;
        if (file.result && file.result.output_filename) {
            filename = file.result.output_filename;
        } else if (file.result && file.result.filename) {
            // Convert input filename to output filename
            const baseName = file.result.filename.replace('.pdf', '');
            // Look for the most recent output file with this base name
            try {
                const response = await fetch('/api/files');
                const result = await response.json();
                if (result.success && result.files) {
                    // Find matching output file
                    const outputFile = result.files.find(f => 
                        f.filename.includes(file.name.replace('.pdf', '')) ||
                        f.filename.includes(baseName.split('_').pop().replace('.pdf', ''))
                    );
                    if (outputFile) {
                        filename = outputFile.filename;
                    }
                }
            } catch (e) {
                console.warn('Could not fetch file list:', e);
            }
        }
        
        // Fallback to generating expected filename
        if (!filename) {
            const baseName = file.name.replace('.pdf', '');
            filename = `${baseName}.txt`;
        }

        if (!filename) {
            this.showNotification('No output file available for download', 'warning');
            return;
        }

        try {
            this.showLoading(true);
            const response = await fetch(`/api/download/${encodeURIComponent(filename)}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                this.showNotification(`Downloaded: ${filename}`, 'success');
            } else {
                const errorText = await response.text();
                this.showNotification(`Download failed: ${response.status} - ${errorText}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Download error: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async downloadAll() {
        try {
            const response = await fetch('/api/download-all');
            
            if (response.ok) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `pdf_extracts_${new Date().toISOString().split('T')[0]}.zip`;
                a.click();
                URL.revokeObjectURL(url);
                this.showNotification('Download started', 'success');
            } else {
                this.showNotification('No files available for download', 'warning');
            }
        } catch (error) {
            this.showNotification(`Download error: ${error.message}`, 'error');
        }
    }

    async checkSystemStatus() {
        try {
            const response = await fetch('/api/health');
            const result = await response.json();
            
            if (result.success && result.system_status) {
                this.updateSystemStatus(result.system_status);
            } else {
                this.updateSystemStatus({ tesseract: false, poppler: false });
            }
        } catch (error) {
            console.error('Failed to check system status:', error);
            this.updateSystemStatus({ tesseract: false, poppler: false });
        }
    }

    updateSystemStatus(status) {
        const tesseractStatus = document.getElementById('tesseract-status');
        const popplerStatus = document.getElementById('poppler-status');
        
        if (tesseractStatus) {
            tesseractStatus.className = `fas fa-circle status-indicator ${status.tesseract ? 'online' : 'offline'}`;
        }
        
        if (popplerStatus) {
            popplerStatus.className = `fas fa-circle status-indicator ${status.poppler ? 'online' : 'offline'}`;
        }
    }

    async loadResults() {
        try {
            const response = await fetch('/api/files');
            const result = await response.json();
            
            if (result.success && result.files) {
                this.results = result.files.map(file => ({
                    id: Date.now() + Math.random(),
                    name: file.filename,
                    size: file.size,
                    timestamp: file.modified,
                    result: { filename: file.filename }
                }));
                this.updateResultsList();
            }
        } catch (error) {
            console.error('Failed to load results:', error);
        }
    }

    handleSearch(e) {
        const query = e.target.value.toLowerCase();
        const rows = document.querySelectorAll('#files-table-body tr:not(.empty-state)');
        
        rows.forEach(row => {
            const fileName = row.querySelector('.file-name')?.textContent.toLowerCase();
            if (fileName && fileName.includes(query)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (show) {
            overlay.classList.add('show');
        } else {
            overlay.classList.remove('show');
        }
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        notification.innerHTML = `
            <div class="notification-header">
                <span class="notification-title">${type.charAt(0).toUpperCase() + type.slice(1)}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="notification-message">${message}</div>
        `;
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new PDFDashboard();
});

// Add some utility functions to window for onclick handlers
window.dashboard = null;
