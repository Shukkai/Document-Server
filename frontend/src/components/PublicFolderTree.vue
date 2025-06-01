<template>
  <div class="folder-tree-container">
    <!-- Error message -->
    <transition name="fade">
      <div v-if="error" class="alert-message alert-error">
        <span class="icon">⚠️</span>
        {{ error }}
        <button class="alert-dismiss" @click="error = null">×</button>
      </div>
    </transition>

    <!-- Success message -->
    <transition name="fade">
      <div v-if="successMessage" class="alert-message alert-success">
        <span class="icon">✅</span>
        {{ successMessage }}
        <button class="alert-dismiss" @click="successMessage = null">×</button>
      </div>
    </transition>

    <!-- Loading indicator -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner"></div>
    </div>

    <div class="folder-tree">
      <div class="folder-item">
        <!-- Folder Header -->
        <div class="folder-header" @click="toggleFolder(0)">
          <div class="folder-info">
            <button class="folder-toggle" :class="{ 'expanded': isFolderExpanded(0) }">
              <span class="toggle-icon">{{ isFolderExpanded(0) ? '▼' : '▶' }}</span>
            </button>
            <span class="folder-icon">📁</span>
            <h3 class="folder-name">Public Folder</h3>
            <span class="folder-stats">
              {{ publicFiles?.length || 0 }} files
            </span>
          </div>
        </div>

        <!-- Folder Contents (collapsible) -->
        <transition name="folder-expand">
          <div v-if="isFolderExpanded(0)" class="folder-contents">
            <!-- Files in this folder -->
            <div v-if="publicFiles?.length > 0" class="files-section">
              <div class="files-grid">
                <div 
                  v-for="file in publicFiles" 
                  :key="file.id" 
                  class="file-card"
                >
                  <!-- File Header -->
                  <div class="file-header" @click="toggleFileInfo(file)">
                    <div class="file-info">
                      <span class="file-icon">{{ getFileIcon(file.mimetype) }}</span>
                      <div class="file-details">
                        <h4 class="file-name" :title="file.name">{{ file.name }}</h4>
                        <div class="file-status">
                          <span class="file-date">{{ formatDate(file.uploaded_at) }}</span>
                        </div>
                      </div>
                    </div>
                    <span class="toggle-icon">{{ file.__showInfo ? '▲' : '▼' }}</span>
                  </div>

                  <!-- File Preview -->
                  <div v-if="file.__showInfo && isPreviewable(file.mimetype)" class="file-preview">
                    <img
                      v-if="file.mimetype?.startsWith('image/')"
                      :src="`${baseURL}/download/${file.id}`"
                      :alt="file.name"
                      class="preview-image"
                    />
                    <div v-else class="pdf-preview">
                      <iframe
                        :src="`${baseURL}/download/${file.id}`"
                        :title="file.name"
                        class="preview-iframe"
                      ></iframe>
                      <div class="pdf-overlay">
                        <span class="pdf-label">PDF Preview</span>
                      </div>
                    </div>
                  </div>

                  <!-- File Actions -->
                  <div v-if="file.__showInfo" class="file-actions">

                    <!-- Action buttons -->
                    <div class="action-buttons">
                      <a
                        :href="`${baseURL}/download/${file.id}`"
                        target="_blank"
                        rel="noopener"
                        :class="{ disabled: isLoading }"
                        class="btn btn-success btn-sm"
                        title="Download file"
                      >
                        <span class="icon">📥</span>
                        Download
                      </a>
                    </div>
                  </div>

                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, defineProps, defineEmits, ref, watch, onMounted } from 'vue'
import axios from 'axios'

/* ---------- props / emits ---------- */
const props = defineProps({ publicFiles: { type: Array, required: true } })
const emit = defineEmits(['refresh-tree'])

/* ---------- state ---------- */
const isLoading = ref(false)
const error = ref(null)
const successMessage = ref(null)
const selectedFile = ref(null)
const editingFile = ref(null)
const expandedFolders = ref(new Set())
const fileToRename = ref(null)
const fileToReview = ref(null)
const users = ref([])
const selectedReviewer = ref(null)
const currentUserIsAdmin = ref(false)

/* ---------- auto-expand root folders ---------- */
watch(() => props.publicFiles, (newpublicFiles) => {
  if (newpublicFiles && newpublicFiles.length > 0) {
    // Automatically expand the root folder if it has children
    expandedFolders.value.add(0) // Assuming 0 is the ID for the root public folder
  } else {
    expandedFolders.value.clear() // Clear if no files are present
  }
}, { immediate: true, deep: true })

onMounted(async () => {
  try {
    // Adjust the endpoint if yours is different (e.g., '/user-info')
    const response = await axios.get('/session-status'); 
    if (response.data && response.data.authenticated && response.data.user) {
      currentUserIsAdmin.value = !!response.data.user.is_admin; // Ensure boolean
    } else {
      // Not authenticated or user data missing, assume not admin
      currentUserIsAdmin.value = false;
    }

    // pollingInterval = setInterval(() =>{
    //   fetchData()
    // }, 1000)
    
  } catch (error) {
    console.error('Error fetching user session status in FolderTree:', error);
    currentUserIsAdmin.value = false; // On error, assume not admin
  }
});

const fetchPublic = async () => {
  const res = await axios.get('/public-files', { withCredentials:true })
  props.publicFiles = res.data || []
}

/* ---------- helpers ---------- */
const baseURL = axios.defaults.baseURL
const isPreviewable = m => m?.startsWith('image/') || m === 'application/pdf'

function getFileIcon(mimetype) {
  if (!mimetype) return '📄'
  if (mimetype.startsWith('image/')) return '🖼️'
  if (mimetype.startsWith('video/')) return '🎥'
  if (mimetype.startsWith('audio/')) return '🎵'
  if (mimetype === 'application/pdf') return '📕'
  if (mimetype.includes('word')) return '📝'
  if (mimetype.includes('excel') || mimetype.includes('spreadsheet')) return '📊'
  if (mimetype.includes('powerpoint') || mimetype.includes('presentation')) return '📈'
  if (mimetype.includes('zip') || mimetype.includes('rar')) return '📦'
  if (mimetype.startsWith('text/')) return '📄'
  return '📄'
}

function formatFileType(mimetype) {
  if (!mimetype) return 'Unknown'
  if (mimetype.startsWith('image/')) return 'Image'
  if (mimetype.startsWith('video/')) return 'Video'
  if (mimetype.startsWith('audio/')) return 'Audio'
  if (mimetype === 'application/pdf') return 'PDF'
  if (mimetype.includes('word')) return 'Document'
  if (mimetype.includes('excel') || mimetype.includes('spreadsheet')) return 'Spreadsheet'
  if (mimetype.includes('powerpoint') || mimetype.includes('presentation')) return 'Presentation'
  if (mimetype.includes('zip') || mimetype.includes('rar')) return 'Archive'
  if (mimetype.startsWith('text/')) return 'Text'
  return 'File'
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/* ---------- expansion ---------- */
function toggleFolder(folderId) {
  if (expandedFolders.value.has(folderId)) {
    expandedFolders.value.delete(folderId)
  } else {
    expandedFolders.value.add(folderId)
  }
}

function isFolderExpanded(folderId) {
  return expandedFolders.value.has(folderId)
}

function toggleFileInfo(file) {
  file.__showInfo = !file.__showInfo
}

/* ---------- helper functions ---------- */
// Helper to check if a file is text-editable by filename extension
const editableTextExtensions = ['.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml', '.html', '.css'];
function isTextEditable(file) {
  if (!file || !file.name) return false;
  const extension = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
  return editableTextExtensions.includes(extension);
  // Or, you could check based on file.mimetype if it's reliable
  // return file.mimetype && file.mimetype.startsWith('text/'); 
}

</script>

<style scoped>
/* ──────────── Container ──────────── */
.folder-tree-container {
  position: relative;
}

.folder-tree {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* ──────────── Folder Item ──────────── */
.folder-item {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.2s ease;
}

.folder-item:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-1px);
}

/* ──────────── Folder Header ──────────── */
.folder-header {
  background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%);
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #cbd5e0;
  cursor: pointer;
  transition: all 0.2s ease;
}

.folder-header:hover {
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e0 100%);
}

.folder-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.folder-toggle {
  background: none;
  border: none;
  padding: 0.25rem;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

.folder-toggle:hover {
  background: rgba(66, 153, 225, 0.1);
}

.toggle-icon {
  font-size: 0.8rem;
  color: #4299e1;
  transition: transform 0.2s ease;
}

.folder-toggle.expanded .toggle-icon {
  transform: rotate(90deg);
}

.folder-icon {
  font-size: 1.5rem;
}

.folder-name {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  color: #2d3748;
}

.folder-stats {
  font-size: 0.85rem;
  color: #718096;
  background: white;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  border: 1px solid #cbd5e0;
}

.folder-actions {
  display: flex;
  gap: 0.5rem;
}

/* ──────────── Files Section ──────────── */
.files-section {
  padding: 1.5rem;
}

.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1rem;
}

/* ──────────── File Card ──────────── */
.file-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s ease;
}

.file-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transform: translateY(-1px);
}

/* ──────────── File Header ──────────── */
.file-header {
  padding: 1rem;
  border-bottom: 1px solid #f1f5f9;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.file-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-name {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #2d3748;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  margin: 0;
  font-size: 0.8rem;
  color: #718096;
}

/* ──────────── File Preview ──────────── */
.file-preview {
  position: relative;
  background: #f7fafc;
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  max-width: 100%;
  max-height: 120px;
  object-fit: contain;
}

.pdf-preview {
  position: relative;
  width: 100%;
  height: 120px;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
  pointer-events: none;
}

.pdf-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.pdf-label {
  background: rgba(0,0,0,0.7);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

/* ──────────── File Actions ──────────── */
.file-actions {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.move-section {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.move-select {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  font-size: 0.9rem;
  background: white;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

/* ──────────── Buttons ──────────── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  white-space: nowrap;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-sm {
  padding: 0.4rem 0.6rem;
  font-size: 0.8rem;
}

.btn-primary {
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(66, 153, 225, 0.3);
}

.btn-success {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  color: white;
}

.btn-success:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(72, 187, 120, 0.3);
}

.btn-info {
  background: linear-gradient(135deg, #38b2ac 0%, #319795 100%);
  color: white;
}

.btn-info:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(56, 178, 172, 0.3);
}

.btn-danger {
  background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
  color: white;
}

.btn-danger:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(245, 101, 101, 0.3);
}

.btn-warning {
  background: linear-gradient(135deg, #ecc94b 0%, #d69e2e 100%);
  color: white;
}

.btn-warning:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(236, 201, 75, 0.3);
}

.btn-secondary {
  background: linear-gradient(135deg, #a0aec0 0%, #718096 100%);
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(160, 174, 192, 0.3);
}

.btn-review {
  background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%);
  color: white;
}

.btn-review:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(124, 58, 237, 0.3);
}

.btn-cancel {
  background: linear-gradient(135deg, #e11d48 0%, #be185d 100%);
  color: white;
}

.btn-cancel:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(225, 29, 72, 0.3);
}

.btn-publish {
  background: linear-gradient(135deg, #f6ad55 0%, #dd6b20 100%);
  color: white;
}

.btn-publish:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(253, 164, 72, 0.3);
}

/* ──────────── No Files ──────────── */
.no-files {
  padding: 2rem;
  text-align: center;
  color: #718096;
}

.no-files .icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 0.5rem;
}

.no-files p {
  margin: 0;
  font-style: italic;
}

/* ──────────── Folder Contents ──────────── */
.folder-contents {
  overflow: hidden;
}

/* ──────────── Subfolder Section ──────────── */
.subfolder-section {
  padding: 0 1.5rem 1.5rem;
  border-top: 1px solid #e2e8f0;
  background: #fafafa;
}

/* ──────────── Alert Message ──────────── */
.alert-message {
  padding: 1rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  border: 1px solid transparent;
}

.alert-error {
  background: #fed7d7; /* Light red */
  color: #c53030;     /* Dark red */
  border-color: #feb2b2; /* Reddish border */
}

.alert-success {
  background: #d4edda; /* Light green */
  color: #155724;     /* Dark green */
  border-color: #c3e6cb; /* Greenish border */
}

.alert-dismiss {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  margin-left: auto;
  opacity: 0.7;
}

.alert-dismiss:hover {
  opacity: 1;
}

/* ──────────── Loading ──────────── */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 100;
}

.loading-spinner {
  width: 30px;
  height: 30px;
  border: 3px solid #e2e8f0;
  border-top: 3px solid #4299e1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* ──────────── Modal ──────────── */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 2rem;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 1400px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0,0,0,0.3);
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
}

.modal-header h3 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #2d3748;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #718096;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: #e2e8f0;
  color: #2d3748;
}

.modal-body {
  padding: 1.5rem;
}

.file-info {
  background: #f7fafc;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.file-info p {
  margin: 0.5rem 0;
}

.file-info strong {
  color: #2d3748;
}

/* ──────────── Animations ──────────── */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.folder-expand-enter-active, .folder-expand-leave-active {
  transition: all 0.3s ease;
  max-height: 1000px;
  opacity: 1;
}

.folder-expand-enter-from, .folder-expand-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-10px);
}

/* ──────────── Icons ──────────── */
.icon {
  display: inline-block;
}

.disabled {
  opacity: 0.5;
  pointer-events: none;
}

/* ──────────── Responsive ──────────── */
@media (max-width: 768px) {
  .files-grid {
    grid-template-columns: 1fr;
  }
  
  .folder-header {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  .folder-info {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .action-buttons {
    justify-content: center;
  }
  
  .move-section {
    flex-direction: column;
  }
  
  .modal-overlay {
    padding: 1rem;
  }
}

/* ──────────── Review Status ──────────── */
.review-status {
  background: #fef3c7;
  color: #92400e;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  border: 1px solid #fcd34d;
}

.file-status {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.file-date {
  font-size: 0.8rem;
  color: #718096;
}

/* ──────────── Review Modal ──────────── */
.review-modal {
  max-width: 500px;
  width: 100%;
  max-width: 600px;
}

.review-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.header-icon {
  font-size: 1.5rem;
}

.header-text {
  flex: 1;
}

.header-text h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  color: #2d3748;
}

.header-text p {
  margin: 0.5rem 0;
  font-size: 0.8rem;
  color: #718096;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #718096;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: #e2e8f0;
  color: #2d3748;
}

.review-body {
  padding: 1.5rem;
}

.review-file-info {
  background: #f7fafc;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.file-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.file-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-name {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #2d3748;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-type {
  margin: 0;
  font-size: 0.8rem;
  color: #718096;
}

.review-selection {
  margin-top: 1rem;
}

.selection-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #2d3748;
}

.select-wrapper {
  position: relative;
}

.select-arrow {
  position: absolute;
  top: 50%;
  right: 1rem;
  transform: translateY(-50%);
}

.select-arrow span {
  font-size: 0.8rem;
  color: #718096;
}

.selection-help {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: #718096;
}

.review-footer {
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  align-items: center;
  background: #fafafa;
}

.modern-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  text-decoration: none;
  min-width: 120px;
  justify-content: center;
}

.modern-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

.btn-secondary.modern-btn {
  background: #f3f4f6;
  color: #374151;
  border: 2px solid #d1d5db;
}

.btn-secondary.modern-btn:hover:not(:disabled) {
  background: #e5e7eb;
  border-color: #9ca3af;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.primary-gradient {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: 2px solid transparent;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.primary-gradient:hover:not(:disabled) {
  background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.btn-icon {
  font-size: 1rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.loading {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>