/**
 * Smart Notebook Print Formatter - Frontend Application
 */

// API Configuration - use relative path for same-origin deployment
const API_BASE = '/api';

// State
const state = {
    sessionId: null,
    uploadedFiles: [],
    currentFile: null,
    preview: null,
    exportOptions: {
        format: 'docx',
        template: 'academic_report.html',
        show_line_numbers: true,
        show_execution_count: false,
        include_outputs: true,
        page_numbers: true,
        toc: true,
    },
};

// DOM Elements
const elements = {
    uploadZone: document.getElementById('upload-zone'),
    fileInput: document.getElementById('file-input'),
    fileList: document.getElementById('file-list'),
    filesContainer: document.getElementById('files-container'),
    previewSection: document.getElementById('preview-section'),
    previewTitle: document.getElementById('preview-title'),
    previewStats: document.getElementById('preview-stats'),
    previewContent: document.getElementById('preview-content'),
    graphsContainer: document.getElementById('graphs-container'),
    optionsSection: document.getElementById('options-section'),
    templateSelect: document.getElementById('template-select'),
    convertBtn: document.getElementById('convert-btn'),
    resultsSection: document.getElementById('results-section'),
    resultDetails: document.getElementById('result-details'),
    downloadBtn: document.getElementById('download-btn'),
    convertAnotherBtn: document.getElementById('convert-another-btn'),
    loadingOverlay: document.getElementById('loading-overlay'),
    loadingText: document.getElementById('loading-text'),
};

// Utility Functions
function showLoading(text = 'Processing...') {
    elements.loadingText.textContent = text;
    elements.loadingOverlay.hidden = false;
}

function hideLoading() {
    elements.loadingOverlay.hidden = true;
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'API request failed');
    }
    
    return response.json();
}

// File Upload
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    if (state.sessionId) {
        formData.append('session_id', state.sessionId);
    }
    
    const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Upload failed');
    }
    
    return response.json();
}

async function handleFileSelect(file) {
    showLoading('Uploading file...');
    
    try {
        const result = await uploadFile(file);
        
        state.sessionId = result.session_id;
        state.uploadedFiles.push({
            name: result.filename,
            size: result.file_size,
        });
        state.currentFile = result.filename;
        
        renderFileList();
        await loadPreview(result.filename);
        
        elements.optionsSection.hidden = false;
        hideLoading();
    } catch (error) {
        hideLoading();
        alert('Upload failed: ' + error.message);
    }
}

function renderFileList() {
    if (state.uploadedFiles.length === 0) {
        elements.fileList.hidden = true;
        return;
    }
    
    elements.fileList.hidden = false;
    elements.filesContainer.innerHTML = state.uploadedFiles.map(file => `
        <div class="file-item fade-in">
            <div class="file-info">
                <div class="file-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                    </svg>
                </div>
                <div>
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${formatFileSize(file.size)}</div>
                </div>
            </div>
            <div class="file-actions">
                <button class="btn btn-small btn-secondary" onclick="selectFile('${file.name}')">
                    Preview
                </button>
                <button class="btn btn-small btn-danger" onclick="removeFile('${file.name}')">
                    Remove
                </button>
            </div>
        </div>
    `).join('');
}

async function loadPreview(filename) {
    showLoading('Loading preview...');
    
    try {
        const preview = await apiCall(`/preview/${state.sessionId}/${filename}`);
        state.preview = preview;
        renderPreview(preview);
        elements.previewSection.hidden = false;
        hideLoading();
    } catch (error) {
        hideLoading();
        console.error('Preview failed:', error);
    }
}

function renderPreview(preview) {
    elements.previewTitle.textContent = preview.title;
    elements.previewStats.textContent = `${preview.total_cells} cells • ${preview.graphs.length} figures`;
    
    // Render cells
    elements.previewContent.innerHTML = preview.cells.map(cell => `
        <div class="preview-cell ${cell.cell_type}">
            ${cell.cell_type === 'code' ? '<code>' : ''}
            ${escapeHtml(cell.source_preview)}
            ${cell.cell_type === 'code' ? '</code>' : ''}
        </div>
    `).join('');
    
    // Render graphs placeholder
    if (preview.graphs.length > 0) {
        document.getElementById('preview-graphs').hidden = false;
        elements.graphsContainer.innerHTML = preview.graphs.map(graph => `
            <div class="graph-thumb" title="${graph.caption}">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <circle cx="8.5" cy="8.5" r="1.5"></circle>
                    <polyline points="21 15 16 10 5 21"></polyline>
                </svg>
            </div>
        `).join('');
    } else {
        document.getElementById('preview-graphs').hidden = true;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function selectFile(filename) {
    state.currentFile = filename;
    loadPreview(filename);
}

function removeFile(filename) {
    state.uploadedFiles = state.uploadedFiles.filter(f => f.name !== filename);
    renderFileList();
    
    if (state.currentFile === filename) {
        state.currentFile = state.uploadedFiles[0]?.name || null;
        if (state.currentFile) {
            loadPreview(state.currentFile);
        } else {
            elements.previewSection.hidden = true;
            elements.optionsSection.hidden = true;
        }
    }
}

// Conversion
async function convertNotebook() {
    if (!state.currentFile) {
        alert('Please upload a file first');
        return;
    }
    
    showLoading('Converting notebook...');
    
    try {
        const result = await apiCall('/convert', {
            method: 'POST',
            body: JSON.stringify({
                session_id: state.sessionId,
                filename: state.currentFile,
                options: state.exportOptions,
            }),
        });
        
        if (result.success) {
            showResults(result);
        } else {
            throw new Error(result.errors.join(', ') || 'Conversion failed');
        }
        
        hideLoading();
    } catch (error) {
        hideLoading();
        alert('Conversion failed: ' + error.message);
    }
}

function showResults(result) {
    elements.resultsSection.hidden = false;
    elements.uploadSection?.scrollIntoView({ behavior: 'smooth' });
    
    const details = [
        result.output_filename,
        formatFileSize(result.file_size),
    ];
    
    if (result.page_count) {
        details.push(`${result.page_count} pages`);
    }
    if (result.graph_count > 0) {
        details.push(`${result.graph_count} figures`);
    }
    
    elements.resultDetails.textContent = details.join(' • ');
    elements.downloadBtn.href = `${API_BASE}${result.output_url}`;
    elements.downloadBtn.download = result.output_filename;
    
    elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function resetApp() {
    state.uploadedFiles = [];
    state.currentFile = null;
    state.preview = null;
    state.sessionId = null;
    
    elements.fileList.hidden = true;
    elements.previewSection.hidden = true;
    elements.optionsSection.hidden = true;
    elements.resultsSection.hidden = true;
    elements.filesContainer.innerHTML = '';
}

// Event Listeners
function initEventListeners() {
    // Upload zone click
    elements.uploadZone.addEventListener('click', () => {
        elements.fileInput.click();
    });
    
    // File input change
    elements.fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFileSelect(file);
        }
        e.target.value = ''; // Reset for re-upload
    });
    
    // Drag and drop
    elements.uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.uploadZone.classList.add('dragover');
    });
    
    elements.uploadZone.addEventListener('dragleave', () => {
        elements.uploadZone.classList.remove('dragover');
    });
    
    elements.uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadZone.classList.remove('dragover');
        
        const file = e.dataTransfer.files[0];
        if (file) {
            handleFileSelect(file);
        }
    });
    
    // Format buttons
    document.querySelectorAll('.format-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.format-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.exportOptions.format = btn.dataset.format;
        });
    });
    
    // Template select
    elements.templateSelect.addEventListener('change', (e) => {
        state.exportOptions.template = e.target.value;
    });
    
    // Options checkboxes
    document.getElementById('opt-line-numbers').addEventListener('change', (e) => {
        state.exportOptions.show_line_numbers = e.target.checked;
    });
    
    document.getElementById('opt-outputs').addEventListener('change', (e) => {
        state.exportOptions.include_outputs = e.target.checked;
    });
    
    document.getElementById('opt-toc').addEventListener('change', (e) => {
        state.exportOptions.toc = e.target.checked;
    });
    
    document.getElementById('opt-page-numbers').addEventListener('change', (e) => {
        state.exportOptions.page_numbers = e.target.checked;
    });
    
    // Convert button
    elements.convertBtn.addEventListener('click', convertNotebook);
    
    // Convert another button
    elements.convertAnotherBtn.addEventListener('click', resetApp);
}

// Make functions available globally
window.selectFile = selectFile;
window.removeFile = removeFile;

// Initialize
document.addEventListener('DOMContentLoaded', initEventListeners);
