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
      <div v-for="folder in folders" :key="folder.id" class="folder-item">
        <!-- Folder Header -->
        <div class="folder-header" @click="toggleFolder(folder.id)">
          <div class="folder-info">
            <button class="folder-toggle" :class="{ 'expanded': isFolderExpanded(folder.id) }">
              <span class="toggle-icon">{{ isFolderExpanded(folder.id) ? '▼' : '▶' }}</span>
            </button>
            <span class="folder-icon">📁</span>
            <h3 class="folder-name">{{ folder.name }}</h3>
            <span class="folder-stats">
              {{ folder.files?.length || 0 }} files
              <span v-if="folder.children?.length">
                • {{ folder.children.length }} subfolders
              </span>
            </span>
          </div>
          
          <div class="folder-actions" @click.stop>
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

        <!-- Folder Contents (collapsible) -->
        <transition name="folder-expand">
          <div v-if="isFolderExpanded(folder.id)" class="folder-contents">
            <!-- Files in this folder -->
            <div v-if="folder.files?.length > 0" class="files-section">
              <div class="files-grid">
                <div 
                  v-for="file in folder.files" 
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
                          <span v-if="file.is_under_review" class="review-status">
                            📋 Under Review by {{ file.active_review.reviewer }}
                          </span>
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
                          :key="opt.id || 'root'"
                          :value="opt.id"
                          :disabled="opt.id === folder.id"
                        >
                          📁 {{ opt.label }}
                        </option>
                      </select>
                      <button
                        class="btn btn-primary btn-sm"
                        :disabled="file.__target === undefined || file.__target === '' || isLoading"
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
                        v-if="isTextEditable(file)"
                        class="btn btn-warning btn-sm"
                        @click="openTextEditor(file)"
                        :disabled="isLoading || file.is_under_review"
                        :title="file.is_under_review ? 'Cannot edit while under review' : 'Edit file content'"
                      >
                        <span class="icon">✏️</span>
                        Edit
                      </button>

                      <button
                        class="btn btn-secondary btn-sm" 
                        @click="openRenameModal(file)"
                        :disabled="isLoading || file.is_under_review"
                        :title="file.is_under_review ? 'Cannot rename while under review' : 'Rename file'"
                      >
                        <span class="icon">🏷️</span>
                        Rename
                      </button>

                      <!-- Review actions -->
                      <button
                        v-if="file.is_under_review"
                        class="btn btn-cancel btn-sm"
                        @click="cancelReview(file)"
                        :disabled="isLoading"
                        title="Cancel review request"
                      >
                        <span class="icon">❌</span>
                        Cancel Review
                      </button>

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
                        :disabled="isLoading || file.is_under_review"
                        :title="file.is_under_review ? 'Cannot delete while under review' : 'Delete file'"
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
            <div v-else-if="!folder.children?.length" class="no-files">
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
        </transition>
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
            :isAdmin="currentUserIsAdmin"
            @success="handleVersionSuccess"
            @error="handleVersionError"
          />
        </div>
      </div>
    </div>

    <!-- Text Editor Modal -->
    <TextEditor
      v-if="editingFile"
      :fileId="editingFile.id"
      :initialFilename="editingFile.name"
      @close="closeTextEditor"
      @save-success="handleSaveSuccess"
      @save-and-review="handleSaveAndReview"
    />

    <!-- Rename File Modal -->
    <RenameFileModal
      v-if="fileToRename"
      :fileId="fileToRename.id"
      :currentFilename="fileToRename.name"
      @close="closeRenameModal"
      @rename-success="handleRenameSuccess"
    />

    <!-- Request Review Modal -->
    <div v-if="fileToReview" class="modal-overlay" @click="closeReviewModal">
      <div class="modal-content review-modal" @click.stop>
        <div class="modal-header review-header">
          <div class="header-content">
            <div class="header-icon">
              <span class="icon">📝</span>
            </div>
            <div class="header-text">
              <h3>Request Review</h3>
              <p class="header-subtitle">Send this document for review</p>
            </div>
          </div>
          <button class="modal-close" @click="closeReviewModal">×</button>
        </div>
        
        <div class="modal-body review-body">
          <div class="file-info review-file-info">
            <div class="file-header">
              <div class="file-icon">
                {{ getFileIcon(fileToReview.mimetype) }}
              </div>
              <div class="file-details">
                <h4 class="file-name">{{ fileToReview.name }}</h4>
                <p class="file-type">{{ formatFileType(fileToReview.mimetype) }}</p>
              </div>
            </div>
          </div>
          
          <div class="reviewer-selection review-selection">
            <label for="reviewer-select" class="selection-label">
              <span class="label-icon">👤</span>
              Select Reviewer
            </label>
            <div class="select-wrapper">
              <select 
                id="reviewer-select" 
                v-model="selectedReviewer" 
                class="reviewer-select modern-select"
                :disabled="isLoading"
              >
                <option value="" disabled>Choose a reviewer...</option>
                <option 
                  v-for="user in users" 
                  :key="user.id" 
                  :value="user.id"
                >
                  {{ user.username }} ({{ user.email }})
                </option>
              </select>
              <div class="select-arrow">
                <span>▼</span>
              </div>
            </div>
            <p class="selection-help">The selected reviewer will be notified about your request</p>
          </div>
        </div>

        <div class="modal-footer review-footer">
          <button 
            class="btn btn-secondary modern-btn" 
            @click="closeReviewModal" 
            :disabled="isLoading"
          >
            <span class="btn-icon">✕</span>
            Cancel
          </button>
          <button 
            class="btn btn-primary modern-btn primary-gradient" 
            @click="requestReview" 
            :disabled="!selectedReviewer || isLoading"
          >
            <span v-if="isLoading" class="btn-icon loading">⏳</span>
            <span v-else class="btn-icon">📤</span>
            <span v-if="isLoading">Sending...</span>
            <span v-else>Send Review Request</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, defineProps, defineEmits, ref, watch, onMounted } from 'vue'
import axios from 'axios'
import FolderTree from './FolderTree.vue'
import FileVersion from './FileVersion.vue'
import TextEditor from './TextEditor.vue'
import RenameFileModal from './RenameFileModal.vue'

/* ---------- props / emits ---------- */
const props = defineProps({ folders: { type: Array, required: true } })
const emit = defineEmits(['delete-folder', 'delete-file', 'refresh-tree'])

/* ---------- auto-expand root folders ---------- */
watch(() => props.folders, (newFolders) => {
  // Auto-expand root folders when they're loaded
  if (newFolders && newFolders.length > 0) {
    newFolders.forEach(folder => {
      if (folder.parent_id === null) {
        expandedFolders.value.add(folder.id)
      }
    })
  }
}, { immediate: true })

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
  } catch (error) {
    console.error('Error fetching user session status in FolderTree:', error);
    currentUserIsAdmin.value = false; // On error, assume not admin
  }
});

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
  const list = [];
  // Add root folder option first (with null ID for moving to root)
  list.push({ id: null, label: 'Root folder' });

  // Helper function to recursively add folders to the list
  function addFoldersRecursively(folders, prefix = '') {
    folders.forEach(folder => {
      // Avoid adding a direct representation of the root folder if it's passed in props.folders
      // especially if props.folders itself is the root and its name is 'root'
      // The generic "Root folder" with id: null is already added.
      if (folder.parent_id === null && (folder.name.toLowerCase() === 'root' || folder.name === 'Root folder')) {
        if (folder.children && folder.children.length > 0) {
          addFoldersRecursively(folder.children, ''); // Start with no prefix for children of actual root
        }
        return; // Skip adding the root object itself as a named option if it's like {name: 'root', ...}
      }

      list.push({ id: folder.id, label: `${prefix}${folder.name}` });
      if (folder.children && folder.children.length > 0) {
        addFoldersRecursively(folder.children, `${prefix}${folder.name}/`);
      }
    });
  }

  // Process props.folders. If props.folders is an array containing the root folder itself,
  // the logic inside addFoldersRecursively will handle its children.
  addFoldersRecursively(props.folders);

  return list.filter((opt, index, self) => 
    index === self.findIndex((o) => o.id === opt.id && o.label === opt.label)
  );
})

/* ---------- folder expansion ---------- */
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

/* ---------- version control ---------- */
function showVersionControl(file) {
  selectedFile.value = file
}

function closeVersionControl() {
  selectedFile.value = null
}

function handleVersionSuccess(message) {
  error.value = null
  successMessage.value = message || 'Version operation completed successfully'
  emit('refresh-tree')
  setTimeout(() => {
    successMessage.value = null
  }, 3000)
}

function handleVersionError(message) {
  successMessage.value = null
  error.value = message || 'Version operation failed'
  setTimeout(() => {
    error.value = null
  }, 5000)
}

/* ---------- text editor functions ---------- */
function openTextEditor(file) {
  editingFile.value = file;
}

function closeTextEditor() {
  editingFile.value = null;
}

function handleSaveSuccess() {
  successMessage.value = 'File content saved successfully!';
  closeTextEditor();
  emit('refresh-tree'); // Refresh folder tree to show updated file stats (e.g., modified date if backend updates it)
   setTimeout(() => {
    successMessage.value = null;
  }, 3000);
}

async function handleSaveAndReview(fileId) {
  try {
    successMessage.value = 'File saved! Opening review request...';
    closeTextEditor();
    
    // Force refresh the tree and wait for it to complete
    emit('refresh-tree');
    
    // Wait longer to ensure the tree has been refreshed with latest data
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Try to find the updated file in the refreshed tree
    const findFileInFolders = (folders, targetId) => {
      for (const folder of folders) {
        if (folder.files) {
          const file = folder.files.find(f => f.id === targetId);
          if (file) return file;
        }
        if (folder.children) {
          const file = findFileInFolders(folder.children, targetId);
          if (file) return file;
        }
      }
      return null;
    };
    
    let file = findFileInFolders(props.folders, fileId);
    
    // If still not found, fetch fresh file data directly from the server
    if (!file) {
      try {
        const response = await axios.get(`/file-content/${fileId}`, { withCredentials: true });
        // Create a minimal file object with the essential data we need
        file = {
          id: fileId,
          name: response.data.filename || 'File',
          filename: response.data.filename || 'File',
          mimetype: response.data.mimetype || 'unknown'
        };
      } catch (error) {
        console.error('Failed to fetch file data:', error);
        // Fallback: create a minimal file object
        file = { 
          id: fileId, 
          name: 'File', 
          filename: 'File', 
          mimetype: 'unknown' 
        };
      }
    }
    
    // Now open the review modal with the updated file data
    openReviewModal(file);
    successMessage.value = null;
    
  } catch (error) {
    console.error('Error in handleSaveAndReview:', error);
    error.value = 'Failed to open review request. Please try again.';
    successMessage.value = null;
    setTimeout(() => {
      error.value = null;
    }, 5000);
  }
}

/* ---------- rename file functions ---------- */
function openRenameModal(file) {
  fileToRename.value = file;
}

function closeRenameModal() {
  fileToRename.value = null;
}

function handleRenameSuccess(eventPayload) {
  successMessage.value = `File renamed to "${eventPayload.newFilename}" successfully!`;
  closeRenameModal();
  emit('refresh-tree'); 
  setTimeout(() => {
    successMessage.value = null;
  }, 3000);
}

/* ---------- review functions ---------- */
async function fetchUsers() {
  try {
    const response = await axios.get('/users', { withCredentials: true })
    users.value = response.data
  } catch (error) {
    console.error('Error fetching users:', error)
    error.value = 'Failed to load users'
  }
}

function openReviewModal(file) {
  fileToReview.value = file
  fetchUsers()
}

function closeReviewModal() {
  fileToReview.value = null
  selectedReviewer.value = null
}

async function requestReview() {
  if (!selectedReviewer.value) {
    error.value = 'Please select a reviewer'
    return
  }

  isLoading.value = true
  error.value = null

  try {
    await axios.post(`/request-review/${fileToReview.value.id}`, {
      reviewer_id: selectedReviewer.value
    }, { withCredentials: true })
    
    successMessage.value = 'Review request sent successfully!'
    closeReviewModal()
    emit('refresh-tree')
    
    setTimeout(() => {
      successMessage.value = null
    }, 3000)
  } catch (e) {
    error.value = e.response?.data?.error || 'Failed to request review'
    setTimeout(() => {
      error.value = null
    }, 5000)
  } finally {
    isLoading.value = false
  }
}

async function cancelReview(file) {
  if (!confirm('Are you sure you want to cancel this review request?')) return

  isLoading.value = true
  error.value = null

  try {
    await axios.post(`/cancel-review/${file.id}`, {}, { withCredentials: true })
    
    successMessage.value = 'Review request cancelled successfully!'
    emit('refresh-tree')
    
    setTimeout(() => {
      successMessage.value = null
    }, 3000)
  } catch (e) {
    error.value = e.response?.data?.error || 'Failed to cancel review'
    setTimeout(() => {
      error.value = null
    }, 5000)
  } finally {
    isLoading.value = false
  }
}

function toggleFileInfo(file) {
  file.__showInfo = !file.__showInfo
}

/* ---------- move file ---------- */
async function move(file) {
  isLoading.value = true
  error.value = null
  successMessage.value = null
  
  try {
    // Handle null value for root folder properly
    const targetFolderId = file.__target === null ? null : file.__target
    
    await axios.post(
      '/move-file',
      { file_id: file.id, target_folder_id: targetFolderId },
      { withCredentials: true }
    )
    file.__target = ''          // reset dropdown after success
    emit('refresh-tree')        // parent reloads -> rerender
    
    successMessage.value = 'File moved successfully!'
    setTimeout(() => {
      successMessage.value = null
    }, 3000)
  } catch (e) {
    error.value = e.response?.data?.error || 'Move failed'
    console.error('Move failed:', e)
    setTimeout(() => {
      error.value = null
    }, 5000)
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
    await axios.delete(`/folders/${folderId}`, { withCredentials: true })
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
  successMessage.value = null
  
  try {
    await axios.delete(`/delete/${fileId}`, { withCredentials: true })
    emit('delete-file', fileId)
    emit('refresh-tree')
    successMessage.value = 'File deleted successfully. Version history is preserved.'
    setTimeout(() => {
      successMessage.value = null
    }, 3000)
  } catch (e) {
    error.value = e.response?.data?.error || 'Delete failed'
    console.error('Delete file failed:', e)
    setTimeout(() => {
      error.value = null
    }, 5000)
  } finally {
    isLoading.value = false
  }
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