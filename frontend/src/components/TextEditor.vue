<template>
  <div class="modal-overlay" @click.self="closeEditor">
    <div class="modal-content text-editor-modal">
      <div class="modal-header">
        <h3>Editing: {{ filename }}</h3>
        <button class="modal-close" @click="closeEditor">×</button>
      </div>
      <div class="modal-body" :class="{ loading: loading, errored: !!error }">
        <QuillEditor 
          v-if="!loading && !error"
          v-model:content="content"
          contentType="html" 
          theme="snow" 
          :toolbar="toolbarOptions"
          class="rich-text-editor"
          placeholder="Start typing or paste your content here..."
        />
        <div v-if="loading" class="loading-spinner-container">
          <div class="loading-spinner"></div>
          <p>Loading file...</p>
        </div>
        <div v-if="error" class="editor-error">
          <p>⚠️ {{ error }}</p>
          <button @click="fetchContent" class="btn btn-sm btn-danger">Retry</button>
        </div>
      </div>
      <div class="modal-footer">
        <div v-if="saveStatus" :class="['save-status', {'success': isSuccess, 'error': !isSuccess}]">
          {{ saveStatus }}
        </div>
        <button class="btn btn-secondary" @click="closeEditor" :disabled="isSaving">
          <span class="icon">❌</span>
          Cancel
        </button>
        <button 
          class="btn btn-primary" 
          @click="saveDraft" 
          :disabled="isSaving || loading || !!error || isContentUnchanged"
          :title="saveButtonTitle"
        >
          <span v-if="isSaving && saveAction === 'draft'" class="icon">⏳</span>
          <span v-else class="icon">💾</span>
          {{ saveButtonText }}
        </button>
        <button 
          class="btn btn-success" 
          @click="saveAndRequestReview" 
          :disabled="isSaving || loading || !!error"
          title="Request a review for this file (will save changes if any)"
        >
          <span v-if="isSaving && saveAction === 'review'" class="icon">⏳</span>
          <span v-else class="icon">📝</span>
          {{ requestReviewButtonText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, defineProps, defineEmits, computed } from 'vue';
import axios from 'axios';
import { QuillEditor } from '@vueup/vue-quill';
import '@vueup/vue-quill/dist/vue-quill.snow.css'; // Import Quill Snow theme CSS

const props = defineProps({
  fileId: { type: Number, required: true },
  initialFilename: { type: String, default: 'file.txt' }
});

const emit = defineEmits(['close', 'save-success', 'save-and-review']);

const content = ref('');
const originalContent = ref(''); // To track changes
const filename = ref(props.initialFilename);
const loading = ref(true);
const error = ref(null);
const isSaving = ref(false);
const saveStatus = ref('');
const isSuccess = ref(false);
const saveAction = ref('draft');

// Basic toolbar options for Quill. You can customize this extensively.
// https://quilljs.com/docs/modules/toolbar/
const toolbarOptions = [
  [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
  [{ 'font': [] }],
  ['bold', 'italic', 'underline', 'strike'], // toggled buttons
  ['blockquote', 'code-block'],

  [{ 'list': 'ordered'}, { 'list': 'bullet' }],
  [{ 'script': 'sub'}, { 'script': 'super' }], // superscript/subscript
  [{ 'indent': '-1'}, { 'indent': '+1' }], // outdent/indent
  [{ 'direction': 'rtl' }], // text direction

  [{ 'size': ['small', false, 'large', 'huge'] }], // custom dropdown
  
  [{ 'color': [] }, { 'background': [] }], // dropdown with defaults from theme
  [{ 'align': [] }],

  ['clean'], // remove formatting button
  ['link', 'image', 'video'] // image and video are for URLs, paste works for base64
];

const isContentUnchanged = computed(() => {
  // Quill might add a default paragraph tag to empty content
  const normalizedCurrentContent = content.value === '<p><br></p>' ? '' : content.value;
  const normalizedOriginalContent = originalContent.value === '<p><br></p>' ? '' : originalContent.value;
  return normalizedCurrentContent === normalizedOriginalContent;
});

const saveButtonText = computed(() => {
  if (isSaving.value && saveAction.value === 'draft') return 'Saving...';
  if (isContentUnchanged.value) return 'No Changes';
  return 'Save';
});

const saveButtonTitle = computed(() => {
  if (isContentUnchanged.value) return 'No changes to save';
  return 'Save changes to file';
});

const requestReviewButtonText = computed(() => {
  if (isSaving.value && saveAction.value === 'review') return 'Processing...';
  if (isContentUnchanged.value) return 'Request Review';
  return 'Save & Request Review';
});

async function fetchContent() {
  loading.value = true;
  error.value = null;
  saveStatus.value = '';
  try {
    const response = await axios.get(`/file-content/${props.fileId}`, { withCredentials: true });
    // Assuming backend sends HTML content now
    content.value = response.data.content || ''; 
    originalContent.value = content.value; // Store initial content for change detection
    filename.value = response.data.filename || props.initialFilename;
  } catch (err) {
    console.error('Error fetching file content:', err);
    error.value = err.response?.data?.error || 'Failed to load file content.';
  } finally {
    loading.value = false;
  }
}

async function saveContent() {
  if (isContentUnchanged.value) {
    saveStatus.value = 'No changes to save.';
    isSuccess.value = true;
    setTimeout(() => { saveStatus.value = '' }, 3000);
    return true; // Return success status
  }
  isSaving.value = true;
  saveStatus.value = '';
  error.value = null; 
  try {
    // Send HTML content to the backend
    await axios.post(`/file-content/${props.fileId}`, { content: content.value }, { withCredentials: true });
    originalContent.value = content.value; // Update original content after successful save
    
    saveStatus.value = 'File saved successfully! You can continue editing or request a review.';
    isSuccess.value = true;
    return true; // Return success status
  } catch (err) {
    console.error('Error saving file content:', err);
    saveStatus.value = err.response?.data?.error || 'Failed to save file.';
    isSuccess.value = false;
    return false; // Return failure status
  } finally {
    isSaving.value = false;
    setTimeout(() => { saveStatus.value = '' }, 3000); 
  }
}

function closeEditor() {
  emit('close');
}

async function saveDraft() {
  saveAction.value = 'draft';
  const success = await saveContent();
  if (success) {
    emit('save-success');
  }
}

async function saveAndRequestReview() {
  saveAction.value = 'review';
  
  // If there are no changes, skip saving and go directly to review request
  if (isContentUnchanged.value) {
    saveStatus.value = 'No changes to save. Opening review request...';
    isSuccess.value = true;
    emit('save-and-review', props.fileId);
    setTimeout(() => closeEditor(), 1500);
    return;
  }
  
  // If there are changes, save first then request review
  try {
    saveStatus.value = 'Saving file...';
    const success = await saveContent();
    
    if (success) {
      saveStatus.value = 'File saved! Preparing review request...';
      
      // Wait a moment to ensure all server-side operations are complete
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Now emit the save-and-review event
      emit('save-and-review', props.fileId);
      setTimeout(() => closeEditor(), 1500);
    }
  } catch (error) {
    console.error('Error in saveAndRequestReview:', error);
    saveStatus.value = 'Failed to save file. Please try again.';
    isSuccess.value = false;
  }
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
  max-width: 900px; /* Wider for rich editor */
  height: 90vh; /* Taller for rich editor */
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
  flex-shrink: 0;
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
  padding: 0; /* Quill will have its own padding if theme provides */
  flex-grow: 1;
  overflow-y: hidden; /* Let Quill handle its own scrolling */
  display: flex;
  flex-direction: column;
  position: relative; /* For spinner positioning */
}
.modal-body.loading, .modal-body.errored {
  padding: 1.5rem; /* Add padding back if showing spinner/error full body */
  overflow-y: auto;
}

.rich-text-editor {
  height: 100%;
  display: flex;
  flex-direction: column; /* Ensure toolbar and content area flow correctly */
  border: none; /* Remove default border if Quill adds one, or style as needed */
}

/* Style Quill editor content area if needed. Default is .ql-container and .ql-editor */
:deep(.ql-toolbar.ql-snow) {
  border-top-left-radius: 6px; /* Match modal style if desired */
  border-top-right-radius: 6px;
  border: 1px solid #ccc;
  border-bottom: none; /* Toolbar is on top */
  padding: 8px;
}
:deep(.ql-container.ql-snow) {
  border-bottom-left-radius: 6px;
  border-bottom-right-radius: 6px;
  border: 1px solid #ccc;
  flex-grow: 1;
  overflow-y: auto; /* Ensure editor content scrolls */
  font-size: 16px; /* Or your preferred base font size */
}
:deep(.ql-editor) {
   min-height: 200px; /* Ensure a minimum editable area */
   padding: 12px;
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
  gap: 1rem;
}

.modal-footer .save-status {
  flex: 1;
  font-size: 0.9rem;
  font-weight: 500;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
}

.modal-footer .save-status.success {
  color: #155724;
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  animation: fadeInSuccess 0.3s ease-in;
}

.modal-footer .save-status.error {
  color: #721c24;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
}

.modal-footer .btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.modal-footer .btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-footer .btn-secondary {
  background: #e2e8f0;
  color: #4a5568;
  order: 1;
}

.modal-footer .btn-secondary:hover:not(:disabled) {
  background: #cbd5e0;
  transform: translateY(-1px);
}

.modal-footer .btn-primary {
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  color: white;
  order: 2;
  box-shadow: 0 2px 4px rgba(66, 153, 225, 0.2);
}

.modal-footer .btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #3182ce 0%, #2c5aa0 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(66, 153, 225, 0.3);
}

.modal-footer .btn-primary:disabled {
  background: #e2e8f0;
  color: #a0aec0;
  cursor: not-allowed;
  box-shadow: none;
}

.modal-footer .btn-success {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  color: white;
  order: 3;
  box-shadow: 0 2px 4px rgba(72, 187, 120, 0.2);
}

.modal-footer .btn-success:hover:not(:disabled) {
  background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(72, 187, 120, 0.3);
}

@keyframes fadeInSuccess {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style> 