<template>
  <div class="files-container">
    <h1>Your files</h1>

    <input type="file" @change="onFileChange" />
    <button :disabled="!selectedFile" @click="upload">Upload</button>

    <ul class="file-list">
      <li v-for="f in files" :key="f.id">
        <span class="fname">{{ f.name || '(no-name)' }}</span>
        <a :href="`${axios.defaults.baseURL}/download/${f.id}`" target="_blank">Download</a>
      </li>
    </ul>

    <button class="logout" @click="logout">Logout</button>
    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios              from 'axios'
import { useRouter }      from 'vue-router'
import { sessionCache }   from '@/router'

const files        = ref([])
const selectedFile = ref(null)
const errorMessage = ref('')
const router       = useRouter()

function onFileChange (e) { selectedFile.value = e.target.files[0] }

async function upload () {
  if (!selectedFile.value) return
  const fd = new FormData()
  fd.append('file', selectedFile.value)
  try {
    await axios.post('/upload', fd, { withCredentials:true })
    await loadFiles()
    selectedFile.value = null
  } catch (err) { handleErr(err) }
}

async function loadFiles () {
  try {
    const { data } = await axios.get('/files', { withCredentials:true })
    files.value = data
  } catch (err) { handleErr(err) }
}

async function logout () {
  await axios.post('/logout', {}, { withCredentials:true })
  sessionCache.value = false   // clear cache
  router.push('/')
}

function handleErr (err) {
  if (err.response?.status === 401) router.push('/')
  else errorMessage.value = err.response?.data?.error || 'Error'
}

onMounted(loadFiles)
</script>

<style scoped>
.files-container { max-width:600px; margin:2rem auto }
.file-list { list-style:none; padding:0; max-height:60vh; overflow:auto }
.file-list li{ display:flex; justify-content:space-between; padding:.4rem .6rem; border-bottom:1px solid #e0e0e0 }
.fname{ flex:1; overflow:hidden; white-space:nowrap; text-overflow:ellipsis }
.logout{ margin-top:1.5rem; background:#e53935; color:#fff; border:none; padding:.5rem .9rem; border-radius:4px; cursor:pointer }
.error{ color:#e53935; margin-top:1rem }
</style>