<template>
  <div class="file-version-container">
    <!-- Version Control Section -->
    <div v-if="!showDeletedFiles" class="version-control">
      <h2>Version Control</h2>
      
      <!-- Upload New Version -->
      <div class="upload-section">
        <h3>Upload New Version</h3>
        <div class="upload-form">
          <input type="file" @change="handleFileSelect" ref="fileInput" />
          <input 
            type="text" 
            v-model="versionComment" 
            placeholder="Version comment (optional)"
            class="comment-input"
          />
          <button @click="uploadNewVersion" :disabled="!selectedFile">
            Upload New Version
          </button>
        </div>
      </div>

      <!-- Version List -->
      <div class="version-list">
        <h3>Version History</h3>
        <div v-if="versions.length === 0" class="no-versions">
          No versions available
        </div>
        <div v-else class="version-table">
          <div class="version-header">
            <span>Version</span>
            <span>Date</span>
            <span>Size</span>
            <span>Comment</span>
            <span>Actions</span>
          </div>
          <div v-for="version in versions" :key="version.version_number" 
               class="version-row" :class="{ 'current-version': version.is_current }">
            <span>v{{ version.version_number }}</span>
            <span>{{ formatDate(version.uploaded_at) }}</span>
            <span>{{ formatSize(version.size) }}</span>
            <span>{{ version.comment || '-' }}</span>
            <span class="actions">
              <button v-if="isPreviewable()" 
                      @click="previewVersion(version)" 
                      class="action-btn preview">
                Preview
              </button>
              <button @click="downloadVersion(version)" class="action-btn">
                Download
              </button>
              <button v-if="isAdmin && !version.is_current" 
                      @click="restoreVersion(version)" 
                      class="action-btn restore">
                Restore
              </button>
              <button v-if="isAdmin && !version.is_current" 
                      @click="deleteVersion(version)" 
                      class="action-btn delete">
                Delete
              </button>
            </span>
          </div>
        </div>
      </div>

      <!-- Version Comparison -->
      <div v-if="selectedVersions.length === 2" class="version-comparison">
        <h3>Version Comparison</h3>
        <div class="comparison-result">
          <pre>{{ comparisonResult }}</pre>
        </div>
      </div>
    </div>

    <!-- Deleted Files Section -->
    <div v-else class="deleted-files">
      <h2>Deleted Files</h2>
      <div class="deleted-files-list">
        <div v-if="deletedFiles.length === 0" class="no-files">
          No deleted files available
        </div>
        <div v-else class="deleted-files-table">
          <div class="deleted-file-header">
            <span>Filename</span>
            <span>Last Modified</span>
            <span>Size</span>
            <span>Last Version</span>
            <span>Actions</span>
          </div>
          <div v-for="file in deletedFiles" :key="file.file_id" class="deleted-file-row">
            <span>{{ file.filename }}</span>
            <span>{{ formatDate(file.last_modified) }}</span>
            <span>{{ formatSize(file.size) }}</span>
            <span>v{{ file.version_number }}</span>
            <span class="actions">
              <button @click="restoreFile(file)" class="action-btn restore">
                Restore
              </button>
              <button @click="permanentlyDeleteFile(file)" class="action-btn delete">
                Delete Permanently
              </button>
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Toggle Button -->
    <button @click="toggleView" class="toggle-view-btn">
      {{ showDeletedFiles ? 'Show Version Control' : 'Show Deleted Files' }}
    </button>

    <!-- Preview Modal -->
    <div v-if="showPreviewModal" class="modal-overlay" @click="closePreviewModal">
      <div class="preview-modal-content" @click.stop>
        <div class="preview-header">
          <h3 v-if="previewContent">
            <span class="icon">👁️</span>
            {{ previewContent.filename }} - v{{ previewContent.version_number }}
          </h3>
          <h3 v-else>Version Preview</h3>
          <button class="modal-close" @click="closePreviewModal">×</button>
        </div>
        
        <div class="preview-body">
          <div v-if="loadingPreview" class="loading-preview">
            <div class="loading-spinner"></div>
            <p>Loading preview...</p>
          </div>
          
          <div v-else-if="previewError" class="error-message">
            <span class="icon">⚠️</span>
            {{ previewError }}
          </div>
          
          <div v-else-if="previewContent" class="preview-content">
            <div class="preview-info">
              <p><strong>Version:</strong> v{{ previewContent.version_number }}</p>
              <p><strong>Comment:</strong> {{ previewContent.comment || 'No comment' }}</p>
              <p><strong>Uploaded:</strong> {{ formatDate(previewContent.uploaded_at) }}</p>
            </div>
            
            <div class="content-display">
              <div class="html-content" v-html="previewContent.content"></div>
            </div>
          </div>
        </div>

        <div class="preview-footer">
          <button class="btn btn-secondary" @click="closePreviewModal">
            Close
          </button>
          <button v-if="previewContent" 
                  class="btn btn-primary" 
                  @click="downloadPreviewedVersion()">
            <span class="icon">📥</span>
            Download This Version
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'FileVersion',
  props: {
    fileId: {
      type: Number,
      required: true
    },
    isAdmin: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      versions: [],
      deletedFiles: [],
      selectedFile: null,
      versionComment: '',
      showDeletedFiles: false,
      selectedVersions: [],
      comparisonResult: null,
      showPreviewModal: false,
      previewContent: null,
      loadingPreview: false,
      previewError: null
    };
  },
  methods: {
    async loadVersions() {
      try {
        const response = await axios.get(`/file-versions/${this.fileId}`);
        this.versions = response.data;
      } catch (error) {
        console.error('Error loading versions:', error);
        this.$emit('error', 'Failed to load versions');
      }
    },
    async loadDeletedFiles() {
      try {
        const response = await axios.get('/list-deleted-files');
        this.deletedFiles = response.data;
      } catch (error) {
        console.error('Error loading deleted files:', error);
        this.$emit('error', 'Failed to load deleted files');
      }
    },
    handleFileSelect(event) {
      this.selectedFile = event.target.files[0];
    },
    async uploadNewVersion() {
      if (!this.selectedFile) return;

      const formData = new FormData();
      formData.append('file', this.selectedFile);
      formData.append('comment', this.versionComment);

      try {
        await axios.post(`/upload-version/${this.fileId}`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        this.$emit('success', 'New version uploaded successfully');
        this.loadVersions();
        this.resetForm();
      } catch (error) {
        console.error('Error uploading version:', error);
        this.$emit('error', 'Failed to upload new version');
      }
    },
    async downloadVersion(version) {
      try {
        const response = await axios.get(
          `/download-version/${this.fileId}/${version.version_number}`,
          { responseType: 'blob' }
        );
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `v${version.version_number}_${this.versions[0].filename}`);
        document.body.appendChild(link);
        link.click();
        link.remove();
      } catch (error) {
        console.error('Error downloading version:', error);
        this.$emit('error', 'Failed to download version');
      }
    },
    async restoreVersion(version) {
      try {
        await axios.post(`/restore-to-version/${this.fileId}/${version.version_number}`);
        this.$emit('success', 'Version restored successfully');
        this.loadVersions();
      } catch (error) {
        console.error('Error restoring version:', error);
        this.$emit('error', 'Failed to restore version');
      }
    },
    async deleteVersion(version) {
      if (!confirm('Are you sure you want to delete this version?')) return;

      try {
        await axios.delete(`/delete-version/${this.fileId}/${version.version_number}`);
        this.$emit('success', 'Version deleted successfully');
        this.loadVersions();
      } catch (error) {
        console.error('Error deleting version:', error);
        this.$emit('error', 'Failed to delete version');
      }
    },
    async restoreFile(file) {
      try {
        await axios.post(`/restore-file/${file.file_id}`);
        this.$emit('success', 'File restored successfully');
        this.loadDeletedFiles();
      } catch (error) {
        console.error('Error restoring file:', error);
        this.$emit('error', 'Failed to restore file');
      }
    },
    async permanentlyDeleteFile(file) {
      if (!confirm('Are you sure you want to permanently delete this file? This cannot be undone.')) return;

      try {
        await axios.delete(`/permanently-delete/${file.file_id}`);
        this.$emit('success', 'File permanently deleted');
        this.loadDeletedFiles();
      } catch (error) {
        console.error('Error deleting file:', error);
        this.$emit('error', 'Failed to delete file');
      }
    },
    async compareVersions(version1, version2) {
      try {
        const response = await axios.get(
          `/compare-versions/${this.fileId}/${version1.version_number}/${version2.version_number}`
        );
        this.comparisonResult = response.data;
      } catch (error) {
        console.error('Error comparing versions:', error);
        this.$emit('error', 'Failed to compare versions');
      }
    },
    toggleView() {
      this.showDeletedFiles = !this.showDeletedFiles;
      if (this.showDeletedFiles) {
        this.loadDeletedFiles();
      } else {
        this.loadVersions();
      }
    },
    resetForm() {
      this.selectedFile = null;
      this.versionComment = '';
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = '';
      }
    },
    formatDate(date) {
      return new Date(date).toLocaleString();
    },
    formatSize(bytes) {
      if (bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    isPreviewable() {
      // Check if the file type is supported for preview
      return true; // We'll handle this in the backend, so always show the button
    },
    async previewVersion(version) {
      this.showPreviewModal = true;
      this.loadingPreview = true;
      this.previewError = null;
      this.previewContent = null;

      try {
        const response = await axios.get(`/version-content/${this.fileId}/${version.version_number}`);
        this.previewContent = response.data;
      } catch (error) {
        console.error('Error loading version preview:', error);
        this.previewError = error.response?.data?.error || 'Failed to load version preview';
      } finally {
        this.loadingPreview = false;
      }
    },
    closePreviewModal() {
      this.showPreviewModal = false;
      this.previewContent = null;
      this.previewError = null;
      this.loadingPreview = false;
    },
    async downloadPreviewedVersion() {
      if (!this.previewContent) return;

      try {
        const response = await axios.get(
          `/download-version/${this.fileId}/${this.previewContent.version_number}`,
          { responseType: 'blob' }
        );
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `v${this.previewContent.version_number}_${this.versions[0].filename}`);
        document.body.appendChild(link);
        link.click();
        link.remove();
      } catch (error) {
        console.error('Error downloading version:', error);
        this.$emit('error', 'Failed to download version');
      }
    }
  },
  mounted() {
    this.loadVersions();
  }
};
</script>

<style scoped>
.file-version-container {
  padding: 0;
  max-width: none;
  margin: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.version-control, .deleted-files {
  background: transparent;
  border-radius: 0;
  padding: 0;
  box-shadow: none;
  margin-bottom: 0;
}

.upload-section {
  margin-bottom: 2.5rem;
  padding: 2rem;
  background: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e9ecef;
}

.upload-section h3 {
  margin-bottom: 1.5rem;
  color: #2d3748;
  font-size: 1.2rem;
  font-weight: 600;
}

.upload-form {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.upload-form input[type="file"] {
  padding: 0.8rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  background: white;
  min-width: 200px;
}

.comment-input {
  flex: 1;
  min-width: 250px;
  padding: 0.8rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.95rem;
  transition: border-color 0.2s ease;
}

.comment-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.upload-form button {
  padding: 0.8rem 1.5rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.upload-form button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.upload-form button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.version-list {
  margin-bottom: 2rem;
}

.version-list h3 {
  margin-bottom: 1.5rem;
  color: #2d3748;
  font-size: 1.2rem;
  font-weight: 600;
}

.version-table, .deleted-files-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.version-header, .deleted-file-header {
  display: grid;
  grid-template-columns: 100px 200px 100px 1fr 350px;
  padding: 1.2rem 1.5rem;
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  font-weight: 600;
  border-bottom: 2px solid #dee2e6;
  color: #2d3748;
  font-size: 0.95rem;
}

.version-row, .deleted-file-row {
  display: grid;
  grid-template-columns: 100px 200px 100px 1fr 350px;
  padding: 1.2rem 1.5rem;
  border-bottom: 1px solid #f1f3f4;
  align-items: center;
  transition: background-color 0.2s ease;
  font-size: 0.9rem;
  min-height: 60px;
}

.version-row:hover, .deleted-file-row:hover {
  background: rgba(102, 126, 234, 0.05);
}

.current-version {
  background: linear-gradient(135deg, #e8f4ff, #f0f8ff) !important;
  border-left: 4px solid #667eea;
}

.actions {
  display: flex;
  gap: 0.8rem;
  flex-wrap: wrap;
  align-items: center;
}

.action-btn {
  padding: 0.6rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s ease;
  min-width: 70px;
  text-align: center;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
}

.action-btn.preview {
  background: linear-gradient(135deg, #17a2b8, #138496);
  color: white;
}

.action-btn.restore {
  background: linear-gradient(135deg, #28a745, #20a038);
  color: white;
}

.action-btn.delete {
  background: linear-gradient(135deg, #dc3545, #c82333);
  color: white;
}

.action-btn:not(.preview):not(.restore):not(.delete) {
  background: linear-gradient(135deg, #6c757d, #5a6268);
  color: white;
}

.toggle-view-btn {
  padding: 1rem 2rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 2rem;
  font-weight: 600;
  font-size: 0.95rem;
  transition: all 0.2s ease;
}

.toggle-view-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.no-versions, .no-files {
  text-align: center;
  padding: 3rem 2rem;
  color: #6c757d;
  background: #f8f9fa;
  border-radius: 12px;
  margin: 1rem 0;
}

.version-comparison {
  margin-top: 2rem;
  padding: 2rem;
  background: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e9ecef;
}

.comparison-result {
  background: #fff;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #dee2e6;
  overflow-x: auto;
  margin-top: 1rem;
}

pre {
  margin: 0;
  white-space: pre-wrap;
  font-size: 0.9rem;
  line-height: 1.5;
}

h2 {
  color: #2d3748;
  margin-bottom: 2rem;
  font-size: 1.5rem;
  font-weight: 700;
}

h3 {
  color: #4a5568;
  margin-bottom: 1.5rem;
  font-size: 1.2rem;
  font-weight: 600;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  backdrop-filter: blur(4px);
  z-index: 2000;
}

.preview-modal-content {
  background: #fff;
  border-radius: 16px;
  width: calc(100vw - 40px);
  max-width: none;
  height: calc(100vh - 40px);
  max-height: calc(100vh - 40px);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2rem 2.5rem;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.preview-header h3 {
  margin: 0;
  color: white;
  font-size: 1.3rem;
}

.preview-body {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.preview-info {
  background: #f7fafc;
  padding: 1.5rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  flex-shrink: 0;
}

.content-display {
  flex: 1;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.5rem;
  overflow-y: auto;
  min-height: 400px;
}

.html-content {
  white-space: pre-wrap;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
  color: #2d3748;
  font-size: 0.95rem;
}

.preview-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-top: 1px solid #e2e8f0;
  background: #f7fafc;
  flex-shrink: 0;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.8rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.2s ease;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #5a6268;
  transform: translateY(-1px);
}

.btn-primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.icon {
  margin-right: 0.3rem;
}

.loading-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 3rem;
}

.loading-spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-top: 4px solid #667eea;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: #dc3545;
  padding: 1.5rem;
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.modal-close {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  font-size: 1.8rem;
  cursor: pointer;
  color: white;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: rotate(90deg);
}

@media (max-width: 768px) {
  .file-version-container {
    padding: 0;
  }
  
  .upload-section {
    padding: 1.5rem;
  }
  
  .upload-form {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }
  
  .version-header, .deleted-file-header {
    grid-template-columns: 80px 150px 80px 1fr 250px;
    padding: 1rem;
    font-size: 0.8rem;
  }
  
  .version-row, .deleted-file-row {
    grid-template-columns: 80px 150px 80px 1fr 250px;
    padding: 1rem;
    font-size: 0.85rem;
    min-height: 50px;
  }
  
  .actions {
    flex-direction: column;
    gap: 0.5rem;
    align-items: stretch;
  }
  
  .action-btn {
    padding: 0.5rem 0.8rem;
    font-size: 0.8rem;
    min-width: auto;
  }
  
  .preview-modal-content {
    width: calc(100vw - 20px);
    height: calc(100vh - 20px);
    border-radius: 12px;
  }
  
  .preview-header, .preview-body, .preview-footer {
    padding: 1.5rem;
  }
  
  .content-display {
    min-height: 250px;
    padding: 1rem;
  }
  
  .btn {
    padding: 0.6rem 1rem;
    font-size: 0.85rem;
  }
}

@media (max-width: 480px) {
  .version-header, .deleted-file-header {
    grid-template-columns: 60px 120px 60px 1fr 180px;
    padding: 0.8rem;
    font-size: 0.75rem;
  }
  
  .version-row, .deleted-file-row {
    grid-template-columns: 60px 120px 60px 1fr 180px;
    padding: 0.8rem;
    font-size: 0.8rem;
    min-height: 45px;
  }
  
  .action-btn {
    padding: 0.4rem 0.6rem;
    font-size: 0.75rem;
  }
}
</style>
