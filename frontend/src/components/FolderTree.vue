<template>
  <ul class="folder-tree">
    <li v-for="folder in folders" :key="folder.id">
      <div class="folder-item">
        📁 {{ folder.name }}
        <button v-if="folder.parent_id !== null" class="delete" @click="$emit('delete-folder', folder.id)">Delete</button>
      </div>

      <!-- FIX: Show this folder's files -->
      <ul class="file-list">
        <li v-for="file in folder.files" :key="file.id">
          <span class="fname">{{ file.name }}</span>
          <div class="actions-inline">
            <a :href="`${baseURL}/download/${file.id}`" target="_blank">Download</a>
            <button class="delete" @click="$emit('delete-file', file.id)">Delete</button>
          </div>
        </li>
      </ul>

      <!-- Recursively show children -->
      <FolderTree
        v-if="folder.children && folder.children.length"
        :folders="folder.children"
        @delete-folder="$emit('delete-folder', $event)"
        @delete-file="$emit('delete-file', $event)"
      />
    </li>
  </ul>
</template>

<script setup>
import FolderTree from './FolderTree.vue'
import axios from 'axios'

defineProps(['folders'])
const baseURL = axios.defaults.baseURL
</script>

<style scoped>
.folder-tree { list-style: none; padding-left: 1rem }
.folder-item { font-weight: bold; display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem }
.file-list { list-style: none; margin-left: 1.5rem; margin-bottom: 0.5rem }
.fname { font-weight: 500 }
.actions-inline { display: flex; gap: 0.5rem }
.delete { background: #757575; color: #fff; border: none; padding: 0.2rem 0.6rem; border-radius: 4px; cursor: pointer }
</style>