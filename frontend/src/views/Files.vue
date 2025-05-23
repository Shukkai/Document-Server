<template>
  <div class="files-container">
    <h1>Your files</h1>

    <input type="file" @change="onFileChange" />
    <button :disabled="!selectedFile" @click="upload">Upload</button>

    <ul class="file-list">
      <li v-for="f in files" :key="f.id">
        <span class="fname">{{ f.name || '(no-name)' }}</span>
        <div class="actions-inline">
          <a :href="`${axios.defaults.baseURL}/download/${f.id}`" target="_blank">Download</a>
          <button class="delete" @click="deleteFile(f.id)">Delete</button>
        </div>
        <div v-if="isPreviewable(f.mimetype)" class="preview">
          <img v-if="f.mimetype.startsWith('image/')" :src="`${axios.defaults.baseURL}/download/${f.id}`" alt="Preview" class="preview-img" />
          <iframe v-else-if="f.mimetype === 'application/pdf'" :src="`${axios.defaults.baseURL}/download/${f.id}`" class="preview-pdf"></iframe>
        </div>
      </li>
    </ul>

    <div class="actions">
      <button class="change-password" @click="changePassword">Change Password</button>
      <button class="logout" @click="logout">Logout</button>
    </div>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    <p v-if="successMessage" class="success">{{ successMessage }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios              from 'axios'
import { useRouter }      from 'vue-router'
import { sessionCache }   from '@/router'

const files          = ref([])
const selectedFile   = ref(null)
const errorMessage   = ref('')
const successMessage = ref('')
const router         = useRouter()

function onFileChange (e) { selectedFile.value = e.target.files[0] }

async function upload () {
  if (!selectedFile.value) return
  const fd = new FormData()
  fd.append('file', selectedFile.value)
  try {
    await axios.post('/upload', fd, { withCredentials:true })
    await loadFiles()
    selectedFile.value = null
    successMessage.value = 'File uploaded successfully.'
    clearMessages()
  } catch (err) { handleErr(err) }
}

async function loadFiles () {
  try {
    const { data } = await axios.get('/files', { withCredentials:true })
    files.value = data
  } catch (err) { handleErr(err) }
}

async function deleteFile (id) {
  try {
    await axios.delete(`/delete/${id}`, { withCredentials:true })
    files.value = files.value.filter(f => f.id !== id)
    successMessage.value = 'File deleted.'
    clearMessages()
  } catch (err) { handleErr(err) }
}

async function logout () {
  await axios.post('/logout', {}, { withCredentials:true })
  sessionCache.value = false
  router.push('/')
  clearMessages()
}

async function changePassword () {
  const currentPassword = prompt('Enter your current password:')
  if (!currentPassword) return

  const newPassword = prompt('Enter your new password (min 6 chars):')

  try {
    await axios.post('/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    }, { withCredentials: true })

    successMessage.value = 'Password changed successfully.'
    errorMessage.value = ''
    clearMessages()
  } catch (err) {
    handleErr(err)
  }
}

function handleErr (err) {
  if (err.response?.status === 401) router.push('/')
  else if (err.response?.status === 413) errorMessage.value = 'File exceeds 25 MB limit'
  else errorMessage.value = err.response?.data?.error || 'Error'
  successMessage.value = ''
  clearMessages()
}

function clearMessages () {
  setTimeout(() => {
    successMessage.value = ''
    errorMessage.value = ''
  }, 5000)
}

function isPreviewable(mime) {
  return mime?.startsWith('image/') || mime === 'application/pdf'
}

onMounted(loadFiles)
</script>

<style scoped>
.files-container { max-width:600px; margin:2rem auto }
.file-list { list-style:none; padding:0; max-height:60vh; overflow:auto }
.file-list li{ display:flex; flex-direction:column; gap:.5rem; padding:.4rem .6rem; border-bottom:1px solid #e0e0e0 }
.fname{ font-weight:600; overflow:hidden; white-space:nowrap; text-overflow:ellipsis }
.actions-inline{ display:flex; gap:1rem; align-items:center }
.preview-img { max-width:100%; max-height:200px; margin-top:.5rem; border:1px solid #ccc }
.preview-pdf { width:100%; height:300px; margin-top:.5rem; border:1px solid #ccc }
.actions{ display:flex; gap:.5rem; margin-top:1.5rem }
.logout{ background:#e53935; color:#fff; border:none; padding:.5rem .9rem; border-radius:4px; cursor:pointer }
.change-password{ background:#1976d2; color:#fff; border:none; padding:.5rem .9rem; border-radius:4px; cursor:pointer }
.delete{ background:#757575; color:#fff; border:none; padding:.3rem .6rem; border-radius:4px; cursor:pointer }
.error{ color:#e53935; margin-top:1rem }
.success{ color:#43a047; margin-top:1rem }
</style>