<template>
  <div class="modal-overlay" @click.self="closeModal">
    <div class="modal-content rename-file-modal">
      <div class="modal-header">
        <h3>Rename File</h3>
        <button class="modal-close" @click="closeModal">×</button>
      </div>
      <div class="modal-body">
        <p>Current name: <strong>{{ currentFilename }}</strong></p>
        <form @submit.prevent="submitRename">
          <div class="form-group">
            <label for="new-filename">New filename:</label>
            <input 
              type="text" 
              id="new-filename" 
              v-model.trim="newFilenameInput" 
              class="form-control" 
              required
              placeholder="Enter new filename (e.g., new_name.txt)"
            />
          </div>
          <div v-if="error" class="error-message">
            ⚠️ {{ error }}
          </div>
        </form>
      </div>
      <div class="modal-footer">
         <div v-if="successMessage" class="success-message">
          ✅ {{ successMessage }}
        </div>
        <button class="btn btn-secondary" @click="closeModal" :disabled="isSaving">Cancel</button>
        <button class="btn btn-primary" @click="submitRename" :disabled="isSaving || !newFilenameInput">
          <span v-if="isSaving" class="icon">⏳</span>
          <span v-else class="icon">💾</span>
          Rename
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, defineProps, defineEmits, watch } from 'vue';
import axios from 'axios';

const props = defineProps({
  fileId: { type: Number, required: true },
  currentFilename: { type: String, required: true }
});

const emit = defineEmits(['close', 'rename-success']);

const newFilenameInput = ref('');
const isSaving = ref(false);
const error = ref(null);
const successMessage = ref(null);

// Watch currentFilename to reset input if the modal is reused for a different file
watch(() => props.currentFilename, (newName) => {
  // Keep existing extension if user hasn't typed one
  // newFilenameInput.value = newName;
}, { immediate: true });

async function submitRename() {
  if (!newFilenameInput.value) {
    error.value = 'New filename cannot be empty.';
    return;
  }
  // Basic extension check - ensure it has one if the original did
  const originalExtension = props.currentFilename.includes('.') ? props.currentFilename.substring(props.currentFilename.lastIndexOf('.')) : '';
  if (originalExtension && !newFilenameInput.value.includes('.')) {
      error.value = `Please include a file extension (e.g., ${originalExtension || '.txt'}).`;
      return;
  } else if (originalExtension && newFilenameInput.value.lastIndexOf('.') < newFilenameInput.value.length -1 && newFilenameInput.value.substring(newFilenameInput.value.lastIndexOf('.')) !== originalExtension) {
      // Optional: Warn if extension changes, or enforce same extension
      // For now, we allow extension changes but this could be a point of validation
  }


  isSaving.value = true;
  error.value = null;
  successMessage.value = null;

  try {
    const response = await axios.post(
      `/rename-file/${props.fileId}`,
      { new_filename: newFilenameInput.value },
      { withCredentials: true }
    );
    successMessage.value = response.data.message || 'File renamed successfully!';
    emit('rename-success', { fileId: props.fileId, newFilename: response.data.new_filename });
    setTimeout(() => closeModal(), 1500); // Auto-close on success
  } catch (err) {
    console.error('Error renaming file:', err);
    error.value = err.response?.data?.error || 'Failed to rename file.';
  } finally {
    isSaving.value = false;
     setTimeout(() => { 
        successMessage.value = null;
        // Do not clear error.value here, let user see it
    }, 4000);
  }
}

function closeModal() {
  newFilenameInput.value = ''; // Reset for next time
  error.value = null;
  successMessage.value = null;
  isSaving.value = false;
  emit('close');
}

</script>

<style scoped>
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex; justify-content: center; align-items: center;
  z-index: 1200; /* Higher than TextEditor */
}

.rename-file-modal {
  background: white; border-radius: 12px;
  width: 90%; max-width: 500px;
  display: flex; flex-direction: column;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}

.modal-header {
  padding: 1rem 1.5rem; border-bottom: 1px solid #e2e8f0;
  display: flex; justify-content: space-between; align-items: center;
}

.modal-header h3 { margin: 0; font-size: 1.2rem; }
.modal-close {
  background: none; border: none; font-size: 1.5rem;
  cursor: pointer; color: #718096;
}

.modal-body {
  padding: 1.5rem;
}

.modal-body p {
  margin-bottom: 1rem;
  font-size: 0.95rem;
  color: #4a5568;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #2d3748;
}

.form-control {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #cbd5e0;
  border-radius: 6px;
  font-size: 0.9rem;
  box-sizing: border-box;
}

.form-control:focus {
  outline: none;
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.2);
}

.error-message {
  color: #c53030;
  background-color: #fed7d7;
  border: 1px solid #feb2b2;
  padding: 0.75rem;
  border-radius: 6px;
  margin-top: 1rem;
  font-size: 0.9rem;
}
.success-message {
  color: #155724;
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  margin-right: auto;
  font-size: 0.9rem;
}

.modal-footer {
  padding: 1rem 1.5rem; border-top: 1px solid #e2e8f0;
  display: flex; justify-content: flex-end; align-items: center;
  gap: 0.75rem;
}

.btn {
  display: inline-flex; align-items: center; gap: 0.3rem;
  padding: 0.6rem 1rem; border: none; border-radius: 6px;
  font-size: 0.9rem; font-weight: 500; cursor: pointer;
  transition: background-color 0.2s ease;
}
.btn:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-primary { background-color: #4299e1; color: white; }
.btn-primary:hover:not(:disabled) { background-color: #3182ce; }

.btn-secondary { background-color: #e2e8f0; color: #2d3748; }
.btn-secondary:hover:not(:disabled) { background-color: #cbd5e0; }

.icon { /* For loading/save icons */ }
</style> 