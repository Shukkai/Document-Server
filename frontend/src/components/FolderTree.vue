<template>
  <div class="folder-tree-container">
    <!-- Error message -->
    <transition name="fade">
      <div v-if="error" class="alert-message">
        <span class="icon">⚠️</span>
        {{ error }}
        <button class="alert-dismiss" @click="error = null">×</button>
      </div>
    </transition>

    <!-- Loading indicator -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner"></div>
    </div>

    <div class="folder-tree">
      <div v-for="folder in folders" :key="folder.id" class="folder-item">
        <!-- Folder Header -->
        <div class="folder-header">
          <div class="folder-info">
            <span class="folder-icon">📁</span>
            <h3 class="folder-name">{{ folder.name }}</h3>
            <span class="folder-stats">
              {{ folder.files?.length || 0 }} files
              <span v-if="folder.children?.length">
                • {{ folder.children.length }} subfolders
              </span>
            </span>
          </div>
          
          <div class="folder-actions">
            <button
              v-if="folder.parent_id !== null"
              class="btn btn-danger btn-sm"
              @click="handleDeleteFolder(folder.id)"
              :disabled="isLoading"
              title="Delete folder"
            >
              <span class="icon">🗑️</span>
              Delete
            </button>
          </div>
        </div>

        <!-- Files in this folder -->
        <div v-if="folder.files?.length > 0" class="files-section">
          <div class="files-grid">
            <div 
              v-for="file in folder.files" 
              :key="file.id" 
              class="file-card"
            >
              <!-- File Header -->
              <div class="file-header">
                <div class="file-info">
                  <span class="file-icon">{{ getFileIcon(file.mimetype) }}</span>
                  <div class="file-details">
                    <h4 class="file-name" :title="file.name">{{ file.name }}</h4>
                    <p class="file-meta">
                      {{ formatFileType(file.mimetype) }}
                      <span v-if="file.uploaded_at">
                        • {{ formatDate(file.uploaded_at) }}
                      </span>
                    </p>
                  </div>
                </div>
              </div>

              <!-- File Preview -->
              <div v-if="isPreviewable(file.mimetype)" class="file-preview">
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
              <div class="file-actions">
                <!-- Move file -->
                <div class="move-section">
                  <select
                    v-model="file.__target"
                    class="move-select"
                    :disabled="isLoading"
                  >
                    <option disabled value="">Move to folder...</option>
                    <option
                      v-for="opt in flatOptions"
                      :key="opt.id"
                      :value="opt.id"
                      :disabled="opt.id === folder.id"
                    >
                      📁 {{ opt.label }}
                    </option>
                  </select>
                  <button
                    class="btn btn-primary btn-sm"
                    :disabled="!file.__target || isLoading"
                    @click="move(file)"
                    title="Move file"
                  >
                    <span class="icon">📤</span>
                  </button>
                </div>

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

                  <button
                    class="btn btn-info btn-sm"
                    @click="showVersionControl(file)"
                    :disabled="isLoading"
                    title="Manage versions"
                  >
                    <span class="icon">📋</span>
                    Versions
                  </button>

                  <button
                    class="btn btn-danger btn-sm"
                    @click="handleDeleteFile(file.id)"
                    :disabled="isLoading"
                    title="Delete file"
                  >
                    <span class="icon">🗑️</span>
                    Delete
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- No files message -->
        <div v-else class="no-files">
          <span class="icon">📂</span>
          <p>This folder is empty</p>
        </div>

        <!-- Recursive children -->
        <div v-if="folder.children?.length" class="subfolder-section">
          <FolderTree
            :folders="folder.children"
            @delete-folder="handleDeleteFolder"
            @delete-file="handleDeleteFile"
            @refresh-tree="$emit('refresh-tree')"
          />
        </div>
      </div>
    </div>

    <!-- Version Control Modal -->
    <div v-if="selectedFile" class="modal-overlay" @click="closeVersionControl">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>
            <span class="icon">📋</span>
            Version Control - {{ selectedFile.name }}
          </h3>
          <button class="modal-close" @click="closeVersionControl">×</button>
        </div>
        
        <div class="modal-body">
          <div class="file-info">
            <p><strong>Type:</strong> {{ selectedFile.mimetype }}</p>
            <p v-if="selectedFile.updated_at">
              <strong>Last Modified:</strong> {{ formatDate(selectedFile.updated_at) }}
            </p>
          </div>
          
          <FileVersion 
            :fileId="selectedFile.id"
            @success="handleVersionSuccess"
            @error="handleVersionError"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, defineProps, defineEmits, ref } from 'vue'
import axios from 'axios'
import FolderTree from './FolderTree.vue'
import FileVersion from './FileVersion.vue'

/* ---------- props / emits ---------- */
const props = defineProps({ folders: { type: Array, required: true } })
const emit = defineEmits(['delete-folder', 'delete-file', 'refresh-tree'])

/* ---------- state ---------- */
const isLoading = ref(false)
const error = ref(null)
const selectedFile = ref(null)

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

/* Flatten tree to build "move" options ---------------------------------- */
function flatten(folder, buffer = [], prefix = '') {
  if (!folder) return buffer
  buffer.push({ id: folder.id, label: `${prefix}${folder.name}` })
  folder.children?.forEach(c =>
    flatten(c, buffer, `${prefix}${folder.name}/`)
  )
  return buffer
}

const flatOptions = computed(() => {
  const list = []
  props.folders.forEach(f => flatten(f, list))
  return list
})

/* ---------- version control ---------- */
function showVersionControl(file) {
  selectedFile.value = file
}

function closeVersionControl() {
  selectedFile.value = null
}

function handleVersionSuccess(message) {
  error.value = null
  emit('refresh-tree')
  // Show success message
  error.value = message || 'Version operation completed successfully'
  setTimeout(() => {
    error.value = null
  }, 3000)
}

function handleVersionError(message) {
  error.value = message || 'Version operation failed'
  setTimeout(() => {
    error.value = null
  }, 5000)
}

/* ---------- move file ---------- */
async function move(file) {
  isLoading.value = true
  error.value = null
  
  try {
    await axios.post(
      '/move-file',
      { file_id: file.id, target_folder_id: file.__target },
      { withCredentials: true }
    )
    file.__target = ''          // reset dropdown after success
    emit('refresh-tree')        // parent reloads -> rerender
  } catch (e) {
    error.value = e.response?.data?.error || 'Move failed'
    console.error('Move failed:', e)
  } finally {
    isLoading.value = false
  }
}

/* ---------- delete handlers ---------- */
async function handleDeleteFolder(folderId) {
  if (!confirm('Are you sure you want to delete this folder?')) return
  
  isLoading.value = true
  error.value = null
  
  try {
    await axios.delete(`/folder/${folderId}`, { withCredentials: true })
    emit('delete-folder', folderId)
    emit('refresh-tree')
  } catch (e) {
    error.value = e.response?.data?.error || 'Delete failed'
    console.error('Delete folder failed:', e)
  } finally {
    isLoading.value = false
  }
}

async function handleDeleteFile(fileId) {
  if (!confirm('Are you sure you want to delete this file? The version history will be preserved.')) return
  
  isLoading.value = true
  error.value = null
  
  try {
    await axios.delete(`/file/${fileId}`, { withCredentials: true })
    emit('delete-file', fileId)
    emit('refresh-tree')
    // Show success message
    error.value = 'File deleted successfully. Version history is preserved.'
    setTimeout(() => {
      error.value = null
    }, 3000)
  } catch (e) {
    error.value = e.response?.data?.error || 'Delete failed'
    console.error('Delete file failed:', e)
  } finally {
    isLoading.value = false
  }
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
}

.folder-info {
  display: flex;
  align-items: center;
  gap: 1rem;
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

/* ──────────── Subfolder Section ──────────── */
.subfolder-section {
  padding: 0 1.5rem 1.5rem;
  border-top: 1px solid #e2e8f0;
  background: #fafafa;
}

/* ──────────── Alert Message ──────────── */
.alert-message {
  background: #fed7d7;
  color: #c53030;
  border: 1px solid #feb2b2;
  padding: 1rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
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
  max-width: 800px;
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
</style>