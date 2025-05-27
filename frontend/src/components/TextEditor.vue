<template>
  <div class="modal-overlay" @click.self="closeEditor">
    <div class="modal-content text-editor-modal">
      <div class="modal-header">
        <h3>Editing: {{ filename }}</h3>
        <button class="modal-close" @click="closeEditor">×</button>
      </div>
      <div class="modal-body">
        <textarea v-if="!loading && !error" v-model="content" class="text-editor-textarea"></textarea>
        <div v-if="loading" class="loading-spinner-container">
          <div class="loading-spinner"></div>
          <p>Loading file...</p>
        </div>
        <div v-if="error" class="editor-error">
          <p>⚠️ {{ error }}</p>
          <button @click="fetchContent">Retry</button>
        </div>
      </div>
      <div class="modal-footer">
        <div v-if="saveStatus" :class="['save-status', {'success': isSuccess, 'error': !isSuccess}]">
          {{ saveStatus }}
        </div>
        <button class="btn btn-secondary" @click="closeEditor" :disabled="isSaving">Cancel</button>
        <button class="btn btn-primary" @click="saveContent" :disabled="isSaving || loading || error">
          <span v-if="isSaving" class="icon">⏳</span>
          <span v-else class="icon">💾</span>
          Save
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, defineProps, defineEmits } from 'vue';
import axios from 'axios';

const props = defineProps({
  fileId: { type: Number, required: true },
  initialFilename: { type: String, default: 'file.txt' }
});

const emit = defineEmits(['close', 'save-success']);

const content = ref('');
const filename = ref(props.initialFilename);
const loading = ref(true);
const error = ref(null);
const isSaving = ref(false);
const saveStatus = ref('');
const isSuccess = ref(false);

async function fetchContent() {
  loading.value = true;
  error.value = null;
  saveStatus.value = '';
  try {
    const response = await axios.get(`/file-content/${props.fileId}`, { withCredentials: true });
    content.value = response.data.content;
    filename.value = response.data.filename || props.initialFilename;
  } catch (err) {
    console.error('Error fetching file content:', err);
    error.value = err.response?.data?.error || 'Failed to load file content.';
  } finally {
    loading.value = false;
  }
}

async function saveContent() {
  isSaving.value = true;
  saveStatus.value = '';
  error.value = null; 
  try {
    await axios.post(`/file-content/${props.fileId}`, { content: content.value }, { withCredentials: true });
    saveStatus.value = 'File saved successfully!';
    isSuccess.value = true;
    emit('save-success');
    setTimeout(() => closeEditor(), 1500); // Auto-close on success
  } catch (err) {
    console.error('Error saving file content:', err);
    saveStatus.value = err.response?.data?.error || 'Failed to save file.';
    isSuccess.value = false;
    error.value = saveStatus.value; // Display save error in main error area too
  } finally {
    isSaving.value = false;
    setTimeout(() => { saveStatus.value = '' }, 4000); // Clear status message
  }
}

function closeEditor() {
  emit('close');
}

onMounted(() => {
  fetchContent();
});

</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1100; /* Higher than FolderTree modal */
}

.text-editor-modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}

.modal-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.2rem;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #718096;
}

.modal-body {
  padding: 1.5rem;
  flex-grow: 1;
  overflow-y: auto; /* Allows textarea to take space and body to scroll if needed */
  display: flex; /* Center loading/error states */
  flex-direction: column;
}

.text-editor-textarea {
  width: 100%;
  height: 100%; /* Take full height of modal-body */
  min-height: 400px; /* Ensure a good default size */
  border: 1px solid #cbd5e0;
  border-radius: 6px;
  padding: 0.75rem;
  font-family: monospace;
  font-size: 0.9rem;
  resize: vertical;
}

.loading-spinner-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top: 4px solid #4299e1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.editor-error {
  color: #c53030;
  text-align: center;
  padding: 1rem;
  background-color: #fed7d7;
  border: 1px solid #feb2b2;
  border-radius: 6px;
  margin: auto; /* Center error box */
}

.editor-error button {
  margin-top: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: #c53030;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 0.75rem;
}

.save-status {
  margin-right: auto; /* Pushes status to the left */
  font-size: 0.9rem;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
}

.save-status.success {
  color: #155724;
  background-color: #d4edda;
}

.save-status.error {
  color: #721c24;
  background-color: #f8d7da;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.6rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #4299e1;
  color: white;
}
.btn-primary:hover:not(:disabled) {
  background-color: #3182ce;
}

.btn-secondary {
  background-color: #e2e8f0;
  color: #2d3748;
}
.btn-secondary:hover:not(:disabled) {
  background-color: #cbd5e0;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style> 