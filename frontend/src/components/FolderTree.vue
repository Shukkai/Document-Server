<template>
  <ul class="folder-tree">
    <li v-for="folder in folders" :key="folder.id">
      <!-- ── folder header ─────────────────────────── -->
      <div class="folder-line">
        <span class="icon">📁</span>
        <span class="name">{{ folder.name }}</span>

        <button
          v-if="folder.parent_id !== null"
          class="btn-sm danger"
          @click="$emit('delete-folder', folder.id)"
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
              :disabled="!file.__target"
              @click="move(file)"
            >
              Go
            </button>

            <a
              :href="`${baseURL}/download/${file.id}`"
              target="_blank"
              rel="noopener"
            >
              Download
            </a>
            <button
              class="btn-sm danger"
              @click="$emit('delete-file', file.id)"
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
        </li>
      </ul>

      <!-- recurse on children -->
      <FolderTree
        v-if="folder.children?.length"
        :folders="folder.children"
        @delete-folder="$emit('delete-folder', $event)"
        @delete-file="$emit('delete-file', $event)"
        @refresh-tree="$emit('refresh-tree')"
      />
    </li>
  </ul>
</template>

<script setup>
import { computed, defineProps, defineEmits } from 'vue'
import axios from 'axios'
import FolderTree from './FolderTree.vue'

/* ---------- props / emits ---------- */
const props = defineProps({ folders: { type: Array, required: true } })
const emit  = defineEmits(['delete-folder', 'delete-file', 'refresh-tree'])

/* ---------- helpers ---------- */
const baseURL = axios.defaults.baseURL
const isPreviewable = m => m?.startsWith('image/') || m === 'application/pdf'

/* Flatten tree to build “move” options ---------------------------------- */
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

/* ---------- move file ---------- */
async function move(file) {
  try {
    await axios.post(
      '/move-file',
      { file_id: file.id, target_folder_id: file.__target },
      { withCredentials: true }
    )
    file.__target = ''          // reset dropdown after success
    emit('refresh-tree')        // parent reloads -> rerender
  } catch (e) {
    alert(e.response?.data?.error || 'Move failed')
  }
}
</script>

<style scoped>
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
</style>