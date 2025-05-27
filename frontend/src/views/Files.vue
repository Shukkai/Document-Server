<!-- src/views/Files.vue -->
<template>
  <div class="files-container">
    <h1>Your files</h1>

    <!-- ───────────── Upload ───────────── -->
    <div class="upload-section">
      <h2>Upload New File</h2>
      <div class="upload-controls">
        <input type="file" @change="onFileChange" />
        <div class="folder-selection">
          <label for="folder-select">Select destination folder:</label>
          <select id="folder-select" v-model="selectedFolderId" class="folder-select">
            <option :value="null">Root folder</option>
            <option v-for="folder in flat" :key="folder.id" :value="folder.id">
              {{ folder.name }}
            </option>
          </select>
        </div>
        <button class="btn upload-btn" :disabled="!selectedFile" @click="upload">Upload</button>
      </div>
      <p class="upload-info">Upload a new file or create a new version of an existing file</p>
    </div>

    <!-- ───────────── Create New Folder ───────────── -->
    <div class="create-folder-section">
      <h2>Create New Folder</h2>
      <div class="create-folder-controls">
        <div class="folder-input-group">
          <label for="folder-name">Folder name:</label>
          <input 
            id="folder-name"
            v-model="newFolderName" 
            placeholder="Enter folder name" 
            class="folder-input"
            @keyup.enter="createFolder"
          />
        </div>
        <div class="parent-folder-selection">
          <label for="parent-folder-select">Create in folder:</label>
          <select id="parent-folder-select" v-model="selectedParentFolderId" class="folder-select">
            <option :value="null">Root folder</option>
            <option v-for="folder in flat" :key="folder.id" :value="folder.id">
              {{ folder.name }}
            </option>
          </select>
        </div>
        <button 
          class="btn create-btn" 
          :disabled="!newFolderName.trim()" 
          @click="createFolder"
        >
          <span class="btn-icon">📁</span>
          Create Folder
        </button>
      </div>
      <p class="create-folder-info">Create a new folder to organize your files</p>
    </div>

    <!-- ───────────── Folders / files ───────────── -->
    <section class="folder-section">
      <h2>Your Folders & Files</h2>

      <!-- recursive tree -->
      <FolderTree
        :folders="folders"
        :flat-folders="flat"
        @delete-folder="deleteFolder"
        @delete-file="deleteFile"
        @move-file="moveFile"
        @refresh-tree="loadFolders"
      />
    </section>

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
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { sessionCache } from '@/router'
import FolderTree from '@/components/FolderTree.vue'

const router = useRouter()

/* ---------------------------------------------------------------- state */
const folders        = ref([])   // nested tree
const flat           = ref([])   // flat list for <select>
const selectedFile   = ref(null)
const selectedFolderId = ref(null) // for upload destination
const selectedParentFolderId = ref(null) // for folder creation parent
const newFolderName  = ref('')
const errorMessage   = ref('')
const successMessage = ref('')
const loading        = ref(false)

/* -------------------------------------------------------------- helpers */
function flash (msg, kind = 'success') {
  if (kind === 'success') successMessage.value = msg
  else                    errorMessage.value   = msg
  setTimeout(() => { successMessage.value = errorMessage.value = '' }, 5000)
}

function handleErr(err) {
  console.error('API Error:', err)
  const message = err.response?.data?.error || err.message || 'An error occurred'
  errorMessage.value = message
}

function onFileChange (e) { 
  const file = e.target.files[0]
  if (file) {
    selectedFile.value = file
    // Clear the input to allow selecting the same file again
    e.target.value = ''
  }
}

/* -------------------------------------------------------------- load tree */
async function loadFolders () {
  try {
    const { data } = await axios.get('/folders', { withCredentials:true })
    
    // Handle new API response structure
    if (data.tree && data.flat) {
      // New API format with tree and flat structure
      const root = Array.isArray(data.tree) ? data.tree : [data.tree]
      folders.value = root
      flat.value = data.flat || []
    } else {
      // Fallback for old API format
      const root = Array.isArray(data) ? data : [data]
      folders.value = root
      // Generate flat list for dropdown (excluding root folder):
      flat.value = []
      function walk(n, depth = 0){ 
        // Skip root folder (parent_id is null)
        if (n.parent_id !== null) {
          const indent = '  '.repeat(depth)
          flat.value.push({id: n.id, name: `${indent}${n.name}`})
        }
        n.children?.forEach(child => walk(child, depth + 1)) 
      }
      root.forEach(walk)
    }
  } catch (err) { handleErr(err) }
}

/* -------------------------------------------------------------- actions */
async function upload () {
  if (!selectedFile.value) return
  const fd = new FormData()
  fd.append('file', selectedFile.value)
  
  // Add folder_id if a folder is selected
  if (selectedFolderId.value) {
    fd.append('folder_id', selectedFolderId.value)
  }
  
  try {
    await axios.post('/upload', fd, { withCredentials:true })
    await loadFolders()
    selectedFile.value = null
    selectedFolderId.value = null // Reset folder selection
    flash('File uploaded successfully')
  } catch (err) { handleErr(err) }
}

async function createFolder () {
  if (!newFolderName.value) return
  try {
    const payload = { 
      name: newFolderName.value,
      parent_id: selectedParentFolderId.value
    }
    await axios.post('/folders', payload, { withCredentials: true })
    
    const parentName = selectedParentFolderId.value 
      ? flat.value.find(f => f.id === selectedParentFolderId.value)?.name || 'Selected folder'
      : 'Root folder'
    
    successMessage.value = `Folder "${newFolderName.value}" created successfully in ${parentName}!`
    newFolderName.value = ''
    selectedParentFolderId.value = null
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

// Move file function
async function moveFile(fileId, folderId) {
  try {
    await axios.post('/move-file', { 
      file_id: fileId, 
      target_folder_id: folderId 
    }, { withCredentials: true })
    successMessage.value = 'File moved successfully!'
    await loadFolders()
    
  } catch (err) {
    console.error('Move file error:', err)
    errorMessage.value = err.response?.data?.error || 'Failed to move file'
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
watch(successMessage, (newVal) => {
  if (newVal) clearMessages()
})

watch(errorMessage, (newVal) => {
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
.folder-section {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.upload-section h2,
.create-folder-section h2,
.folder-section h2 {
  margin: 0 0 1rem 0;
  color: #333;
}

.upload-area {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.upload-controls {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.folder-selection {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.folder-selection label {
  font-weight: 600;
  color: #333;
  font-size: 0.9rem;
}

.create-folder-controls {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.folder-input-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.folder-input-group label,
.parent-folder-selection label {
  font-weight: 600;
  color: #333;
  font-size: 0.9rem;
}

.parent-folder-selection {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.create-folder-info {
  margin: 0;
  font-size: 0.9rem;
  color: #666;
  font-style: italic;
}

.btn-icon {
  font-size: 1rem;
  margin-right: 0.3rem;
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
  padding: 0.75rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s ease;
  background: white;
}

.folder-input:focus {
  outline: none;
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
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
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.create-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(72, 187, 120, 0.3);
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

button:hover {
  background: #1565c0;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* ──────────── Responsive Design ──────────── */
@media (max-width: 768px) {
  .upload-controls,
  .create-folder-controls {
    gap: 0.75rem;
  }
  
  .upload-section,
  .create-folder-section,
  .folder-section {
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }
  
  .folder-input {
    font-size: 16px; /* Prevents zoom on iOS */
  }
}
</style>