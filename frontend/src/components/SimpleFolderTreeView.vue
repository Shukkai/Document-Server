<template>
  <div class="simple-folder-tree">
    <div v-for="item in processedTreeData" :key="item.id || item.name" class="tree-item">
      <div @click="toggle(item)" class="item-header" :style="{ 'padding-left': depth * 20 + 'px' }">
        <span class="toggle-icon">{{ item.type === 'folder' && (item.children?.length || item.files?.length) ? (isOpen(item) ? '▼' : '▶') : '' }}</span>
        <span class="item-icon">{{ item.type === 'folder' ? '📁' : getFileIcon(item.mimetype) }}</span>
        <span class="item-name">{{ item.name }}</span>
        <span v-if="item.type === 'file'" class="item-actions">
          <button @click.stop="showVersions(item)" class="btn-versions">Versions</button>
        </span>
      </div>
      <div v-if="item.type === 'folder' && isOpen(item)" class="item-children">
        <!-- Recursively render child folders -->
        <SimpleFolderTreeView 
          v-if="item.children && item.children.length"
          :treeData="item.children" 
          :depth="depth + 1"
          @show-versions="emitShowVersions"
        />
        <!-- Render files in this folder -->
        <SimpleFolderTreeView 
          v-if="item.files && item.files.length"
          :treeData="item.files" 
          :depth="depth + 1"
          @show-versions="emitShowVersions"
         />
      </div>
    </div>
     <div v-if="!processedTreeData || processedTreeData.length === 0" class="no-content">
      <p>{{ depth === 0 ? 'No files or folders for this user.' : 'Folder is empty.' }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineProps, defineEmits } from 'vue';

const props = defineProps({
  treeData: { // Expects an array of folder or file objects
    type: Array,
    required: true
  },
  depth: {
    type: Number,
    default: 0
  }
});

const emit = defineEmits(['show-versions']);

const openItems = ref(new Set());

// Process tree data to add missing 'type' properties and normalize structure
const processedTreeData = computed(() => {
  if (!props.treeData) return [];
  
  return props.treeData.map(item => {
    // If item doesn't have a type, determine it based on structure
    if (!item.type) {
      // If it has 'children' or 'files' properties, it's a folder
      // If it has 'mimetype' or 'filename', it's a file
      if (item.children !== undefined || item.files !== undefined || item.parent_id !== undefined) {
        return {
          ...item,
          type: 'folder',
          name: item.name
        };
      } else if (item.mimetype !== undefined || item.filename !== undefined) {
        return {
          ...item,
          type: 'file',
          name: item.name || item.filename
        };
      }
    }
    return item;
  });
});

function toggle(item) {
  if (item.type !== 'folder') return;
  const itemId = item.id || item.name; // Use name as fallback if ID is missing for some reason
  if (openItems.value.has(itemId)) {
    openItems.value.delete(itemId);
  } else {
    openItems.value.add(itemId);
  }
}

function isOpen(item) {
  return openItems.value.has(item.id || item.name);
}

function getFileIcon(mimetype) {
  if (!mimetype) return '📄';
  if (mimetype.startsWith('image/')) return '🖼️';
  if (mimetype.startsWith('video/')) return '🎥';
  if (mimetype.startsWith('audio/')) return '🎵';
  if (mimetype === 'application/pdf') return '📕';
  if (mimetype.startsWith('text/')) return '📄';
  return '📄';
}

function showVersions(file) {
  emit('show-versions', file);
}

function emitShowVersions(file) { // Helper to bubble up event from nested component
  emit('show-versions', file);
}

</script>

<style scoped>
.simple-folder-tree {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 0.95rem;
}

.tree-item {
  border-radius: 8px;
  margin-bottom: 2px;
  overflow: hidden;
  transition: all 0.2s ease;
}

.tree-item:hover {
  background-color: rgba(102, 126, 234, 0.05);
}

.item-header {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s ease;
  position: relative;
}

.item-header:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  transform: translateX(4px);
}

.item-header:active {
  transform: translateX(2px);
}

.toggle-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #667eea;
  font-weight: 600;
  margin-right: 0.5rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.toggle-icon:hover {
  background: rgba(102, 126, 234, 0.1);
  transform: scale(1.1);
}

.item-icon {
  margin-right: 0.75rem;
  font-size: 1.2rem;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1));
  transition: transform 0.2s ease;
}

.item-header:hover .item-icon {
  transform: scale(1.05);
}

.item-name {
  flex-grow: 1;
  font-weight: 500;
  color: #2d3748;
  line-height: 1.4;
}

.item-actions {
  margin-left: 1rem;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.item-header:hover .item-actions {
  opacity: 1;
}

.item-actions button {
  padding: 0.4rem 0.8rem;
  font-size: 0.8rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.2);
}

.item-actions button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
  background: linear-gradient(135deg, #5a67d8, #6b46c1);
}

.item-actions button:active {
  transform: translateY(0);
}

.btn-versions {
  background: linear-gradient(135deg, #4299e1, #3182ce) !important;
}

.btn-versions:hover {
  background: linear-gradient(135deg, #3182ce, #2c5aa0) !important;
}

.item-children {
  position: relative;
  border-left: 2px solid rgba(102, 126, 234, 0.2);
  margin-left: 1rem;
  padding-left: 0.5rem;
  transition: all 0.3s ease;
}

.item-children::before {
  content: '';
  position: absolute;
  left: -2px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(180deg, transparent, rgba(102, 126, 234, 0.3), transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.tree-item:hover .item-children::before {
  opacity: 1;
}

.no-content {
  padding: 2rem 1rem;
  text-align: center;
  color: #718096;
  background: rgba(113, 128, 150, 0.05);
  border: 2px dashed rgba(113, 128, 150, 0.2);
  border-radius: 12px;
  margin: 1rem 0;
  font-style: italic;
}

.no-content p {
  margin: 0;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.no-content p::before {
  content: '📂';
  font-size: 1.5rem;
  opacity: 0.5;
}

/* File type specific styling */
.item-header[data-file-type="image"] .item-icon {
  filter: drop-shadow(0 1px 3px rgba(0, 150, 255, 0.3));
}

.item-header[data-file-type="video"] .item-icon {
  filter: drop-shadow(0 1px 3px rgba(255, 0, 100, 0.3));
}

.item-header[data-file-type="audio"] .item-icon {
  filter: drop-shadow(0 1px 3px rgba(150, 0, 255, 0.3));
}

.item-header[data-file-type="pdf"] .item-icon {
  filter: drop-shadow(0 1px 3px rgba(255, 100, 0, 0.3));
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .item-header {
    padding: 0.6rem 0.8rem;
  }
  
  .item-actions {
    opacity: 1; /* Always show on mobile */
  }
  
  .item-actions button {
    font-size: 0.75rem;
    padding: 0.3rem 0.6rem;
  }
  
  .item-children {
    margin-left: 0.5rem;
    padding-left: 0.3rem;
  }
}

@media (max-width: 480px) {
  .simple-folder-tree {
    font-size: 0.9rem;
  }
  
  .item-header {
    padding: 0.5rem;
  }
  
  .item-icon {
    margin-right: 0.5rem;
    font-size: 1.1rem;
  }
  
  .toggle-icon {
    width: 20px;
    height: 20px;
    margin-right: 0.3rem;
  }
}
</style> 