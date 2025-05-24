<template>
  <div class="files-container">
    <h1>Your files</h1>

    <!-- upload -------------------------------------------------------------->
    <input type="file" @change="onFileChange" />
    <button :disabled="!selectedFile" @click="upload">Upload</button>

    <!-- folders / files ----------------------------------------------------->
    <section class="folder-section">
      <h2>Folders</h2>

      <!-- recursive tree component -->
      <FolderTree
        :folders="folders"
        @delete-folder="deleteFolder"
        @delete-file="deleteFile"
      />

      <!-- create folder -->
      <input v-model="newFolderName" placeholder="New folder name" />
      <button @click="createFolder">Create Folder</button>
    </section>

    <!-- account actions ----------------------------------------------------->
    <div class="actions">
      <button class="change-password" @click="changePassword">Change Password</button>
      <button class="logout" @click="logout">Logout</button>
    </div>

    <!-- flash messages ------------------------------------------------------>
    <p v-if="errorMessage"   class="error"  >{{ errorMessage }}</p>
    <p v-if="successMessage" class="success">{{ successMessage }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted }      from 'vue'
import axios                   from 'axios'
import { useRouter }           from 'vue-router'
import { sessionCache }        from '@/router'
import FolderTree              from '@/components/FolderTree.vue'

/* ------------------------------------------------------------------- state */
const folders        = ref([])       // ← array consumed by FolderTree
const selectedFile   = ref(null)
const newFolderName  = ref('')
const errorMessage   = ref('')
const successMessage = ref('')
const router         = useRouter()

/* ------------------------------------------------------------------- utils */
function onFileChange (e) { selectedFile.value = e.target.files[0] }

function flash (msg, type = 'success') {
  successMessage.value = type === 'success' ? msg : ''
  errorMessage.value   = type === 'error'   ? msg : ''
  setTimeout(() => { successMessage.value = errorMessage.value = '' }, 5_000)
}

/* ------------------------------------------------------------------- CRUD */
async function loadFolders () {
  try {
    const { data }   = await axios.get('/folders', { withCredentials:true })
    folders.value    = Array.isArray(data) ? data : [data]   // ✅ wrap root
  } catch (err) { handleErr(err) }
}

async function upload () {
  if (!selectedFile.value) return
  const fd = new FormData();  fd.append('file', selectedFile.value)
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
    flash('Folder created')
  } catch (err) { handleErr(err) }
}

async function deleteFolder (id) {
  try {
    await axios.delete(`/folders/${id}`, { withCredentials:true })
    await loadFolders()
    flash('Folder deleted')
  } catch (err) { handleErr(err) }
}

async function deleteFile (id) {
  try {
    await axios.delete(`/delete/${id}`, { withCredentials:true })
    await loadFolders()
    flash('File deleted')
  } catch (err) { handleErr(err) }
}

/* --------------------------------------------------------- account actions */
async function changePassword () {
  const cur = prompt('Current password:')
  if (!cur) return
  const neu = prompt('New password (min 6 chars):')
  if (!neu) return
  try {
    await axios.post('/change-password', { current_password:cur, new_password:neu }, { withCredentials:true })
    flash('Password changed')
  } catch (err) { handleErr(err) }
}

async function logout () {
  await axios.post('/logout', {}, { withCredentials:true })
  sessionCache.value = false
  router.push('/')
}

/* ---------------------------------------------------------------- handlers */
function handleErr (err) {
  if (err.response?.status === 401) return router.push('/')
  if (err.response?.status === 413) return flash('File exceeds 25 MB limit', 'error')
  flash(err.response?.data?.error || 'Error', 'error')
}

/* ------------------------------------------------------------------- init */
onMounted(loadFolders)
</script>

<style scoped>
.files-container { max-width:640px; margin:2rem auto }
.folder-section  { margin-top:2rem }
.actions         { display:flex; gap:.5rem; margin-top:1.5rem }

.logout, .change-password, .delete {
  border:none; border-radius:4px; cursor:pointer; color:#fff; padding:.45rem .9rem
}
.logout          { background:#e53935 }
.change-password { background:#1976d2 }

.error   { color:#e53935; margin-top:1rem }
.success { color:#43a047; margin-top:1rem }
</style>