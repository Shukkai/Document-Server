<!-- src/views/Files.vue -->
<template>
  <div class="files-page">
    <header class="header">
      <h1>📁 File Manager</h1>
      <div class="user-actions">
        <button @click="logout" class="btn logout-btn">🚪 Logout</button>
      </div>
    </header>

    <main class="main-content">
      <!-- Debug info -->
      <div class="debug-info">
        <p>Loaded: {{ folders.length }} folders, {{ flat.length }} flat folders</p>
        <p>Status: {{ loading ? 'Loading...' : 'Ready' }}</p>
        <p v-if="error" class="error">Error: {{ error }}</p>
      </div>

      <!-- Upload Section -->
      <section class="upload-section">
        <h2>📤 Upload Files</h2>
        <div class="upload-area">
          <input 
            type="file" 
            multiple 
            @change="onFileSelect" 
            class="file-input"
          >
          <p v-if="selectedFiles.length > 0">
            Selected: {{ selectedFiles.length }} files
          </p>
          
          <select v-model="targetFolderId" class="folder-select">
            <option value="">📁 Root Folder</option>
            <option 
              v-for="folder in flat" 
              :key="folder.id" 
              :value="folder.id"
            >
              📁 {{ folder.name }}
            </option>
          </select>
          
          <button 
            @click="uploadFiles" 
            :disabled="selectedFiles.length === 0"
            class="btn upload-btn"
          >
            🚀 Upload
          </button>
        </div>
      </section>

      <!-- Create Folder Section -->
      <section class="create-folder-section">
        <h2>➕ Create New Folder</h2>
        <div class="create-folder-form">
          <input 
            v-model="newFolderName" 
            placeholder="Folder name..."
            class="folder-input"
            @keyup.enter="createFolder"
          >
          <button 
            @click="createFolder" 
            :disabled="!newFolderName.trim()"
            class="btn create-btn"
          >
            Create
          </button>
        </div>
      </section>

      <!-- Folders Display -->
      <section class="folders-section">
        <h2>📂 Your Folders and Files</h2>
        <div v-if="loading" class="loading">Loading folders...</div>
        <div v-else-if="folders.length === 0" class="no-folders">
          No folders found. Create your first folder above!
        </div>
        <div v-else class="folders-list">
          <div v-for="folder in folders" :key="folder.id" class="folder-item">
            <div class="folder-header">
              <h3>📁 {{ folder.name }}</h3>
              <button 
                v-if="folder.parent_id !== null" 
                @click="deleteFolder(folder.id)"
                class="btn delete-btn"
              >
                🗑️ Delete
              </button>
            </div>
            
            <div v-if="folder.files && folder.files.length > 0" class="files-list">
              <div 
                v-for="file in folder.files" 
                :key="file.id" 
                class="file-item"
              >
                <span class="file-icon">📄</span>
                <span class="file-name">{{ file.name }}</span>
                <div class="file-actions">
                  <a 
                    :href="`/download/${file.id}`" 
                    target="_blank"
                    class="btn download-btn"
                  >
                    📥 Download
                  </a>
                  <button 
                    @click="deleteFile(file.id)"
                    class="btn delete-btn"
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
            </div>
            
            <div v-else class="no-files">
              This folder is empty
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Success/Error Messages -->
    <div v-if="successMessage" class="alert success">
      ✅ {{ successMessage }}
      <button @click="successMessage = ''" class="alert-close">×</button>
    </div>
    
    <div v-if="errorMessage" class="alert error">
      ⚠️ {{ errorMessage }}
      <button @click="errorMessage = ''" class="alert-close">×</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { sessionCache } from '@/router'

const router = useRouter()

// State
const folders = ref([])
const flat = ref([])
const selectedFiles = ref([])
const targetFolderId = ref('')
const newFolderName = ref('')
const successMessage = ref('')
const errorMessage = ref('')
const loading = ref(false)
const error = ref('')

// Load folders from backend
async function loadFolders() {
  loading.value = true
  error.value = ''
  
  try {
    console.log('Loading folders...')
    const response = await axios.get('/folders', { withCredentials: true })
    console.log('Response:', response.data)
    
    const data = response.data
    if (!data) {
      console.log('No data received')
      folders.value = []
      flat.value = []
      return
    }
    
    // Handle single root folder or array
    const rootFolders = Array.isArray(data) ? data : [data]
    folders.value = rootFolders
    
    // Build flat list for dropdown
    flat.value = []
    function buildFlat(folder) {
      if (folder && folder.id && folder.name) {
        flat.value.push({ id: folder.id, name: folder.name })
        if (folder.children && Array.isArray(folder.children)) {
          folder.children.forEach(buildFlat)
        }
      }
    }
    
    rootFolders.forEach(buildFlat)
    console.log('Folders loaded:', folders.value)
    console.log('Flat folders:', flat.value)
    
  } catch (err) {
    console.error('Error loading folders:', err)
    error.value = err.response?.data?.error || 'Failed to load folders'
    if (err.response?.status === 401) {
      sessionCache.value = false
      router.push('/')
    }
  } finally {
    loading.value = false
  }
}

// File selection
function onFileSelect(event) {
  const files = Array.from(event.target.files)
  selectedFiles.value = files
  console.log('Selected files:', files)
}

// Upload files
async function uploadFiles() {
  if (selectedFiles.value.length === 0) return
  
  try {
    for (const file of selectedFiles.value) {
      const formData = new FormData()
      formData.append('file', file)
      
      if (targetFolderId.value) {
        formData.append('folder_id', targetFolderId.value)
      }
      
      await axios.post('/upload', formData, { withCredentials: true })
    }
    
    successMessage.value = `${selectedFiles.value.length} file(s) uploaded successfully!`
    selectedFiles.value = []
    document.querySelector('.file-input').value = ''
    await loadFolders()
    
  } catch (err) {
    console.error('Upload error:', err)
    errorMessage.value = err.response?.data?.error || 'Upload failed'
  }
}

// Create folder
async function createFolder() {
  const name = newFolderName.value.trim()
  if (!name) return
  
  try {
    await axios.post('/folders', { name }, { withCredentials: true })
    successMessage.value = `Folder "${name}" created successfully!`
    newFolderName.value = ''
    await loadFolders()
    
  } catch (err) {
    console.error('Create folder error:', err)
    errorMessage.value = err.response?.data?.error || 'Failed to create folder'
  }
}

// Delete folder
async function deleteFolder(id) {
  if (!confirm('Are you sure you want to delete this folder?')) return
  
  try {
    await axios.delete(`/folders/${id}`, { withCredentials: true })
    successMessage.value = 'Folder deleted successfully!'
    await loadFolders()
    
  } catch (err) {
    console.error('Delete folder error:', err)
    errorMessage.value = err.response?.data?.error || 'Failed to delete folder'
  }
}

// Delete file
async function deleteFile(id) {
  if (!confirm('Are you sure you want to delete this file?')) return
  
  try {
    await axios.delete(`/delete/${id}`, { withCredentials: true })
    successMessage.value = 'File deleted successfully!'
    await loadFolders()
    
  } catch (err) {
    console.error('Delete file error:', err)
    errorMessage.value = err.response?.data?.error || 'Failed to delete file'
  }
}

// Logout
async function logout() {
  try {
    await axios.post('/logout', {}, { withCredentials: true })
    sessionCache.value = false
    router.push('/')
  } catch (err) {
    console.error('Logout error:', err)
  }
}

// Clear messages after 5 seconds
function clearMessages() {
  setTimeout(() => {
    successMessage.value = ''
    errorMessage.value = ''
  }, 5000)
}

// Watch for messages and clear them
const unwatchSuccess = $watch(successMessage, (newVal) => {
  if (newVal) clearMessages()
})

const unwatchError = $watch(errorMessage, (newVal) => {
  if (newVal) clearMessages()
})

// Load folders on mount
onMounted(() => {
  console.log('Files component mounted')
  loadFolders()
})
</script>

<style scoped>
.files-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
}

.header {
  background: white;
  padding: 1rem 2rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.header h1 {
  margin: 0;
  color: #333;
  font-size: 1.8rem;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
}

.debug-info {
  background: rgba(255,255,255,0.9);
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 2rem;
  font-size: 0.9rem;
}

.debug-info .error {
  color: #e53e3e;
  font-weight: bold;
}

.upload-section,
.create-folder-section,
.folders-section {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.upload-section h2,
.create-folder-section h2,
.folders-section h2 {
  margin: 0 0 1rem 0;
  color: #333;
}

.upload-area {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.file-input {
  padding: 0.5rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
}

.folder-select {
  padding: 0.75rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  background: white;
}

.create-folder-form {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.folder-input {
  flex: 1;
  padding: 0.75rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.upload-btn {
  background: #4299e1;
  color: white;
}

.upload-btn:hover:not(:disabled) {
  background: #3182ce;
}

.create-btn {
  background: #48bb78;
  color: white;
}

.create-btn:hover:not(:disabled) {
  background: #38a169;
}

.logout-btn {
  background: #f56565;
  color: white;
}

.logout-btn:hover {
  background: #e53e3e;
}

.delete-btn {
  background: #f56565;
  color: white;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
}

.delete-btn:hover {
  background: #e53e3e;
}

.download-btn {
  background: #48bb78;
  color: white;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  text-decoration: none;
}

.download-btn:hover {
  background: #38a169;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.no-folders,
.no-files {
  text-align: center;
  padding: 2rem;
  color: #666;
  font-style: italic;
}

.folders-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.folder-item {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.folder-header {
  background: #f7fafc;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
}

.folder-header h3 {
  margin: 0;
  color: #333;
}

.files-list {
  padding: 1rem;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f1f5f9;
}

.file-item:last-child {
  border-bottom: none;
}

.file-icon {
  font-size: 1.2rem;
}

.file-name {
  flex: 1;
  color: #333;
}

.file-actions {
  display: flex;
  gap: 0.5rem;
}

.alert {
  position: fixed;
  top: 2rem;
  right: 2rem;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  z-index: 1000;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.alert.success {
  background: #c6f6d5;
  color: #22543d;
  border: 1px solid #9ae6b4;
}

.alert.error {
  background: #fed7d7;
  color: #742a2a;
  border: 1px solid #feb2b2;
}

.alert-close {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  margin-left: 0.5rem;
}

@media (max-width: 768px) {
  .files-page {
    padding: 1rem;
  }
  
  .header {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  .create-folder-form {
    flex-direction: column;
  }
  
  .file-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .file-actions {
    width: 100%;
    justify-content: center;
  }
}
</style>