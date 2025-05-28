<!-- src/views/Files.vue -->
<template>
  <div class="files-page-container">
    <header class="top-nav-header">
      <div class="logo-area">
        <span class="logo-icon">☁️</span> 
        <h1>Cloud Document Center</h1>
      </div>
      <nav class="top-nav">
        <button 
          :class="['nav-button', { active: activeView === 'home' }]" 
          @click="setActiveView('home')"
        >
          <span class="icon">🏠</span> Home (Files & Folders)
        </button>
        <button 
          :class="['nav-button', { active: activeView === 'upload' }]" 
          @click="setActiveView('upload')"
        >
          <span class="icon">📤</span> Upload File
        </button>
        <button 
          :class="['nav-button', { active: activeView === 'createFolder' }]" 
          @click="setActiveView('createFolder')"
        >
          <span class="icon">📁</span> Create Folder
        </button>
        <!-- Admin Dashboard Button - Only show for admin users -->
        <button 
          v-if="isAdmin" 
          :class="['nav-button', 'admin-button']" 
          @click="goToAdminDashboard"
        >
          <span class="icon">👑</span> Admin Dashboard
        </button>
        <button class="nav-button" @click="goToUserInfo">
          <span class="icon">👤</span> User Info
        </button>
         <button class="nav-button logout-button" @click="logout">
          <span class="icon">🚪</span> Logout
        </button>
      </nav>
    </header>

    <main class="main-content-area">
      <!-- Conditionally rendered sections -->
      <div v-if="activeView === 'upload'" class="upload-section content-section">
        <h2>Upload New File</h2>
        <div class="upload-controls">
          <input type="file" @change="onFileChange" class="file-input"/>
          <div class="folder-selection">
            <label for="folder-select">Select destination folder:</label>
            <select id="folder-select" v-model="selectedFolderId" class="folder-select">
              <option :value="null">Root folder</option>
              <option v-for="folder in flat" :key="folder.id" :value="folder.id">
                {{ folder.name }}
              </option>
            </select>
          </div>
          <button class="btn upload-btn" :disabled="!selectedFile || loading" @click="upload">
            <span v-if="loading && selectedFile" class="icon">⏳</span>
            <span v-else class="icon">📤</span>
            Upload
          </button>
        </div>
        <p class="upload-info">Upload a new file or create a new version of an existing file.</p>
      </div>

      <div v-if="activeView === 'createFolder'" class="create-folder-section content-section">
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
            :disabled="!newFolderName.trim() || loading" 
            @click="createFolder"
          >
            <span v-if="loading && newFolderName.trim()" class="icon">⏳</span>
            <span v-else class="icon">📁</span>
            Create Folder
          </button>
        </div>
        <p class="create-folder-info">Create a new folder to organize your files.</p>
      </div>

      <section v-if="activeView === 'home'" class="folder-section content-section">
        <h2>Your Folders & Files</h2>
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
      <div v-if="successMessage" class="alert success app-message">
        ✅ {{ successMessage }}
        <button @click="successMessage = ''" class="alert-close">×</button>
      </div>
      <div v-if="errorMessage" class="alert error app-message">
        ⚠️ {{ errorMessage }}
        <button @click="errorMessage = ''" class="alert-close">×</button>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { sessionCache, setSession, startSessionMonitoring, stopSessionMonitoring } from '@/router'
import FolderTree from '@/components/FolderTree.vue'

const router = useRouter()

/* ---------------------------------------------------------------- state */
const activeView = ref('home')
const folders        = ref([])   // nested tree
const flat           = ref([])   // flat list for <select>
const selectedFile   = ref(null)
const selectedFolderId = ref(null) // for upload destination
const selectedParentFolderId = ref(null) // for folder creation parent
const newFolderName  = ref('')
const errorMessage   = ref('')
const successMessage = ref('')
const loading        = ref(false)
const isAdmin        = ref(false)

/* ----------------------------------------------------------- view control */
function setActiveView(viewName) {
  activeView.value = viewName
}

// Check if current user is admin
async function checkAdminStatus() {
  try {
    const response = await axios.get('/session-status', { withCredentials: true })
    if (response.data && response.data.authenticated && response.data.user) {
      isAdmin.value = !!response.data.user.is_admin
      console.log('Admin status:', isAdmin.value, 'User:', response.data.user)
    } else {
      isAdmin.value = false
    }
  } catch (error) {
    console.error('Error checking admin status:', error)
    isAdmin.value = false
  }
}

function goToAdminDashboard() {
  router.push('/admin-dashboard')
}

/* -------------------------------------------------------------- helpers */
function flash (msg, kind = 'success') {
  if (kind === 'success') successMessage.value = msg
  else                    errorMessage.value   = msg
  setTimeout(() => { successMessage.value = errorMessage.value = '' }, 5000)
}

function handleErr(err) {
  loading.value = false
  console.error('API Error:', err)
  const message = err.response?.data?.error || err.message || 'An error occurred'
  flash(message, 'error')
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
  loading.value = true
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
  } catch (err) { handleErr(err) } finally { loading.value = false }
}

/* -------------------------------------------------------------- actions */
async function upload () {
  if (!selectedFile.value) return
  loading.value = true
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
    setActiveView('home') // Switch to home view after upload
  } catch (err) { handleErr(err) } finally { loading.value = false }
}

async function createFolder () {
  if (!newFolderName.value) return
  loading.value = true
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
    setActiveView('home') // Switch to home view after creation
  } catch (err) {
    console.error('Create folder error:', err)
    errorMessage.value = err.response?.data?.error || 'Failed to create folder'
  } finally { loading.value = false }
}

// Delete folder
async function deleteFolder(id) {
  if (!confirm('Are you sure you want to delete this folder?')) return
  
  loading.value = true
  try {
    await axios.delete(`/folders/${id}`, { withCredentials: true })
    successMessage.value = 'Folder deleted successfully!'
    await loadFolders()
    
  } catch (err) {
    console.error('Delete folder error:', err)
    errorMessage.value = err.response?.data?.error || 'Failed to delete folder'
  } finally { loading.value = false }
}

// Delete file
async function deleteFile(id) {
  if (!confirm('Are you sure you want to delete this file?')) return
  
  loading.value = true
  try {
    await axios.delete(`/delete/${id}`, { withCredentials: true })
    successMessage.value = 'File deleted successfully!'
    await loadFolders()
    
  } catch (err) {
    console.error('Delete file error:', err)
    errorMessage.value = err.response?.data?.error || 'Failed to delete file'
  } finally { loading.value = false }
}

// Move file function
async function moveFile(fileId, folderId) {
  loading.value = true
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
  } finally { loading.value = false }
}

// Logout
async function logout() {
  loading.value = true
  try {
    await axios.post('/logout', {}, { withCredentials: true })
    stopSessionMonitoring() // Stop session monitoring
    setSession(false, null) // Clear session and user data
    router.push('/')
  } catch (err) {
    console.error('Logout error:', err)
    // Even if logout fails on server, clear local session
    stopSessionMonitoring()
    setSession(false, null)
    router.push('/')
  } finally { 
    loading.value = false 
  }
}

function goToUserInfo() {
  router.push('/user-info')
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
  checkAdminStatus() // Check if user is admin
  // Set initial view, perhaps from query param or local storage in future
  setActiveView('home')
  startSessionMonitoring()
})

onUnmounted(() => {
  console.log('Files component unmounted')
  stopSessionMonitoring()
})
</script>

<style scoped>
.files-page-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #f4f7f6; /* Light neutral background for the page */
}

.top-nav-header {
  background: #ffffff; /* Clearer background - white */
  color: #2d3748; /* Darker text for contrast */
  padding: 0.75rem 2rem; /* Slightly adjusted padding */
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0; /* Subtle bottom border for separation */
  position: sticky;
  top: 0;
  z-index: 1000;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.logo-icon {
  font-size: 1.7rem; /* Slightly adjusted */
  color: #4299e1; /* Icon color - can be brand blue */
}

.top-nav-header h1 {
  margin: 0;
  font-size: 1.3rem; /* Slightly adjusted */
  font-weight: 600;
  color: inherit; /* Inherits from .top-nav-header */
}

.top-nav {
  display: flex;
  gap: 0.25rem; /* Tighter spacing for a cleaner look */
}

.nav-button {
  background-color: transparent;
  color: #4a5568; /* Darker gray for nav buttons */
  border: none; /* Remove border for a cleaner look initially */
  padding: 0.6rem 1rem; /* Adjusted padding */
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.9rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  border-bottom: 2px solid transparent; /* For active state indicator */
}

.nav-button:hover {
  background-color: #edf2f7; /* Light gray hover */
  color: #2d3748; /* Darker text on hover */
}

.nav-button.active {
  color: #3b82f6; /* Blue for active text */
  border-bottom: 2px solid #3b82f6; /* Blue bottom border for active state */
  background-color: transparent; /* Ensure no competing background */
}

.logout-button {
  margin-left: 1rem;
  color: #e53e3e; /* Red for logout text */
  background-color: transparent;
}

.logout-button:hover {
  background-color: #fed7d7; /* Light red hover background */
  color: #c53030; /* Darker red on hover */
  border-bottom-color: transparent; /* Ensure no blue line from .nav-button.active if it was active */
}

.admin-button {
  background-color: #ffc107 !important; /* Yellow background for admin */
  color: #212529 !important; /* Dark text */
  font-weight: 600 !important;
  border: 2px solid #ffc107 !important;
}

.admin-button:hover {
  background-color: #e0a800 !important; /* Darker yellow on hover */
  color: #000 !important;
  border-color: #e0a800 !important;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(255, 193, 7, 0.3);
}

.main-content-area {
  padding: 2rem;
  flex-grow: 1;
}

.content-section {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.content-section h2 {
  font-size: 1.6rem;
  font-weight: 600;
  color: #2d3748;
  margin-top: 0;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
}

/* Input and select styling common to upload/create folder */
.file-input,
.folder-input,
.folder-select {
  padding: 0.75rem;
  border: 1px solid #cbd5e0;
  border-radius: 6px;
  font-size: 0.9rem;
  margin-bottom: 1rem; /* Spacing */
  box-sizing: border-box;
  width: 100%;
}

.upload-controls,
.create-folder-controls {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.folder-selection,
.parent-folder-selection,
.folder-input-group {
  display: flex;
  flex-direction: column;
}

.folder-selection label,
.parent-folder-selection label,
.folder-input-group label {
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #4a5568;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-size: 0.95rem;
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

.upload-btn,
.create-btn {
  background: linear-gradient(135deg, #38a169 0%, #48bb78 100%); /* Green gradient */
  color: white;
  align-self: flex-start; /* Align button to the start of flex container */
}

.upload-btn:hover:not(:disabled),
.create-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}

.upload-info,
.create-folder-info {
  margin-top: 1rem;
  font-size: 0.85rem;
  color: #718096;
}

.app-message {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1050;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  max-width: 400px;
}

.alert.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.alert.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.alert-close {
  background: none; border: none; font-size: 1.2rem;
  cursor: pointer; margin-left: 1rem; opacity: 0.7;
  color: inherit;
}
.alert-close:hover { opacity: 1; }

.icon { /* General icon styling if needed */ }

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