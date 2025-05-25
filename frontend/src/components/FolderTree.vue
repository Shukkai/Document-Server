<template>
  <div class="folder-tree-container">
    <!-- Error message -->
    <div v-if="error" class="error-message">
      {{ error }}
      <button class="btn-sm" @click="error = null">Dismiss</button>
    </div>

    <!-- Loading indicator -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner"></div>
    </div>

    <ul class="folder-tree">
      <li v-for="folder in folders" :key="folder.id">
        <!-- ── folder header ─────────────────────────── -->
        <div class="folder-line">
          <span class="icon">📁</span>
          <span class="name">{{ folder.name }}</span>

          <button
            v-if="folder.parent_id !== null"
            class="btn-sm danger"
            @click="handleDeleteFolder(folder.id)"
            :disabled="isLoading"
          >
            Delete
          </button>
        </div>

        <!-- ── files in this folder ──────────────────── -->
        <ul class="file-list">
          <li v-for="file in folder.files" :key="file.id">
            <div class="file-line">
              <span class="name">{{ file.name }}</span>

              <!-- Move-to dropdown -->
              <select
                v-model="file.__target"
                class="move-select"
                :disabled="isLoading"
              >
                <option disabled value="">Move ▾</option>
                <option
                  v-for="opt in flatOptions"
                  :key="opt.id"
                  :value="opt.id"
                  :disabled="opt.id === folder.id"
                >
                  {{ opt.label }}
                </option>
              </select>
              <button
                class="btn-sm"
                :disabled="!file.__target || isLoading"
                @click="move(file)"
              >
                Go
              </button>

              <a
                :href="`${baseURL}/download/${file.id}`"
                target="_blank"
                rel="noopener"
                :class="{ disabled: isLoading }"
                class="btn-sm"
              >
                Download
              </a>

              <button
                class="btn-sm"
                @click="showVersionControl(file)"
                :disabled="isLoading"
              >
                Versions
              </button>

              <button
                class="btn-sm danger"
                @click="handleDeleteFile(file.id)"
                :disabled="isLoading"
              >
                Delete
              </button>
            </div>

            <!-- Preview (images + PDFs) -->
            <div v-if="isPreviewable(file.mimetype)" class="preview">
              <img
                v-if="file.mimetype.startsWith('image/')"
                :src="`${baseURL}/download/${file.id}`"
                alt="preview"
              />
              <iframe
                v-else
                :src="`${baseURL}/download/${file.id}`"
                title="pdf preview"
              ></iframe>
            </div>

            <!-- Version Control Modal -->
            <div v-if="selectedFile && selectedFile.id === file.id" class="version-modal">
              <div class="modal-content">
                <button class="close-btn" @click="closeVersionControl">&times;</button>
                <div class="modal-header">
                  <h3>Version Control - {{ file.name }}</h3>
                  <p class="file-info">
                    Type: {{ file.mimetype }} | 
                    Last Modified: {{ new Date(file.updated_at).toLocaleString() }}
                  </p>
                </div>
                <FileVersion 
                  :fileId="file.id"
                  @success="handleVersionSuccess"
                  @error="handleVersionError"
                />
              </div>
            </div>
          </li>
        </ul>

        <!-- recurse on children -->
        <FolderTree
          v-if="folder.children?.length"
          :folders="folder.children"
          @delete-folder="handleDeleteFolder"
          @delete-file="handleDeleteFile"
          @refresh-tree="$emit('refresh-tree')"
        />
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed, defineProps, defineEmits, watch, ref } from 'vue'
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
.folder-tree-container { position: relative; }
.folder-tree { list-style: none; padding-left: 1rem }
.folder-line { display: flex; gap: .5rem; align-items: center; font-weight: 600 }
.file-list   { list-style: none; margin-left: 1.5rem }
.file-line   { display: flex; gap: .5rem; align-items: center }
.icon        { width: 1.2rem }
.btn-sm      { padding: .15rem .5rem; border: none; border-radius: 4px; cursor: pointer }
.danger      { background: #e53935; color: #fff }
.move-select { padding: .15rem .4rem }
.preview img     { max-width: 160px; max-height: 160px; border: 1px solid #ccc }
.preview iframe  { width: 160px; height: 160px; border: 1px solid #ccc }

/* Version Modal */
.version-modal {
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
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  position: relative;
  width: 90%;
  max-width: 1200px;
  max-height: 90vh;
  overflow-y: auto;
}

.close-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.close-btn:hover {
  color: #000;
}

/* Error and Loading styles */
.error-message {
  background: #ffebee;
  color: #c62828;
  padding: 0.5rem;
  margin-bottom: 1rem;
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.loading-spinner {
  width: 30px;
  height: 30px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.disabled {
  opacity: 0.5;
  pointer-events: none;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.modal-header {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.file-info {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}
</style>