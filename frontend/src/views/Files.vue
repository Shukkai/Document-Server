<!-- src/views/Files.vue -->
<template>
  <div class="files-container">
    <h1>Your files</h1>

    <!-- ───────────── Upload ───────────── -->
    <div class="upload-section">
      <h2>Upload New File</h2>
      <div class="upload-controls">
        <input type="file" @change="onFileChange" />
        <button :disabled="!selectedFile" @click="upload">Upload</button>
      </div>
      <p class="upload-info">Upload a new file or create a new version of an existing file</p>
    </div>

    <!-- ───────────── Folders / files ───────────── -->
    <section class="folder-section">
      <h2>Folders</h2>

      <!-- recursive tree -->
      <FolderTree
        :folders="folders"
        :flat-folders="flat"
        @delete-folder="deleteFolder"
        @delete-file="deleteFile"
        @move-file="moveFile"
        @refresh-tree="loadFolders"
      />

      <!-- create folder -->
      <div class="folder-controls">
        <input v-model="newFolderName" placeholder="New folder name" />
        <button @click="createFolder">Create Folder</button>
      </div>
    </section>

    <!-- ───────────── Account actions ───────────── -->
    <div class="actions">
      <button class="change-password" @click="changePassword">Change Password</button>
      <button class="logout"          @click="logout">Logout</button>
    </div>

    <!-- flash messages -->
    <p v-if="errorMessage"   class="error"  >{{ errorMessage }}</p>
    <p v-if="successMessage" class="success">{{ successMessage }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted }  from 'vue'
import axios               from 'axios'
import { useRouter }       from 'vue-router'
import { sessionCache }    from '@/router'
import FolderTree          from '@/components/FolderTree.vue'

/* ---------------------------------------------------------------- state */
const folders        = ref([])   // nested tree
const flat           = ref([])   // flat list for <select>
const selectedFile   = ref(null)
const newFolderName  = ref('')
const errorMessage   = ref('')
const successMessage = ref('')
const router         = useRouter()

/* -------------------------------------------------------------- helpers */
function flash (msg, kind = 'success') {
  if (kind === 'success') successMessage.value = msg
  else                    errorMessage.value   = msg
  setTimeout(() => { successMessage.value = errorMessage.value = '' }, 5000)
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
    const root     = Array.isArray(data) ? data : [data]   // ensure array
    folders.value  = root
    // flat list for dropdown:
    flat.value     = []
    function walk(n){ flat.value.push({id:n.id, name:n.name}); n.children?.forEach(walk) }
    root.forEach(walk)
  } catch (err) { handleErr(err) }
}

/* -------------------------------------------------------------- actions */
async function upload () {
  if (!selectedFile.value) return
  const fd = new FormData()
  fd.append('file', selectedFile.value)
  try {
    await axios.post('/upload', fd, { withCredentials:true })
    await loadFolders()
    selectedFile.value = null
    flash('File uploaded successfully')
  } catch (err) { handleErr(err) }
}

async function createFolder () {
  if (!newFolderName.value) return
  try {
    await axios.post('/folders', { name:newFolderName.value }, { withCredentials:true })
    newFolderName.value = ''
    await loadFolders()
    flash('Folder created successfully')
  } catch (err) { handleErr(err) }
}

async function deleteFolder (id) {
  if (!confirm('Are you sure you want to delete this folder? All files and subfolders will be deleted.')) return
  try { 
    await axios.delete(`/folders/${id}`, { withCredentials:true })
    await loadFolders()
    flash('Folder deleted successfully')
  } catch (err) { handleErr(err) }
}

async function deleteFile (id) {
  if (!confirm('Are you sure you want to delete this file? The version history will be preserved.')) return
  try { 
    await axios.delete(`/delete/${id}`, { withCredentials:true })
    await loadFolders()
    flash('File deleted successfully. Version history is preserved.')
  } catch (err) { handleErr(err) }
}

async function moveFile ({ id, target }) {
  try {
    await axios.post('/move-file', { file_id:id, target_folder_id:target }, { withCredentials:true })
    await loadFolders()
    flash('File moved successfully')
  } catch (err) { handleErr(err) }
}

/* -------------------------------------------------------------- account */
async function changePassword () {
  const cur = prompt('Current password:')
  if (!cur) return
  const neu = prompt('New password (min 6 chars):')
  if (!neu) return
  try { 
    await axios.post('/change-password', { current_password:cur, new_password:neu }, { withCredentials:true })
    flash('Password changed successfully')
  } catch (err) { handleErr(err) }
}

async function logout () {
  await axios.post('/logout', {}, { withCredentials:true })
  sessionCache.value = false
  router.push('/')
}

/* -------------------------------------------------------------- error */
function handleErr (err) {
  if (err.response?.status === 401) return router.push('/')
  if (err.response?.status === 413) return flash('File exceeds 25 MB limit','error')
  flash(err.response?.data?.error || 'Error', 'error')
}

onMounted(loadFolders)
</script>

<style scoped>
.files-container { 
  max-width: 800px; 
  margin: 2rem auto;
  padding: 0 1rem;
}

.upload-section {
  background: #f5f5f5;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.upload-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin: 1rem 0;
}

.upload-info {
  color: #666;
  font-size: 0.9rem;
  margin: 0;
}

.folder-section { 
  margin-top: 2rem;
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.folder-controls {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.actions { 
  display: flex; 
  gap: 1rem; 
  margin-top: 2rem;
  justify-content: flex-end;
}

.logout, .change-password {
  border: none;
  border-radius: 4px;
  cursor: pointer;
  color: #fff;
  padding: 0.6rem 1.2rem;
  font-weight: 500;
  transition: opacity 0.2s;
}

.logout:hover, .change-password:hover {
  opacity: 0.9;
}

.logout { 
  background: #e53935;
}

.change-password { 
  background: #1976d2;
}

.error { 
  color: #e53935;
  margin-top: 1rem;
  padding: 0.75rem;
  background: #ffebee;
  border-radius: 4px;
}

.success { 
  color: #43a047;
  margin-top: 1rem;
  padding: 0.75rem;
  background: #e8f5e9;
  border-radius: 4px;
}

h1 {
  margin: 0 0 1.5rem 0;
  color: #333;
}

h2 {
  margin: 0;
  color: #444;
  font-size: 1.2rem;
}

input[type="file"] {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
}

input[type="text"] {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  flex: 1;
}

button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  background: #1976d2;
  color: white;
  cursor: pointer;
  transition: background-color 0.2s;
}

button:hover {
  background: #1565c0;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>