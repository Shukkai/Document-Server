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
              <button @click="downloadVersion(version)" class="action-btn">
                Download
              </button>
              <button v-if="!version.is_current" 
                      @click="restoreVersion(version)" 
                      class="action-btn restore">
                Restore
              </button>
              <button v-if="!version.is_current" 
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
      comparisonResult: null
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
    }
  },
  mounted() {
    this.loadVersions();
  }
};
</script>

<style scoped>
.file-version-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.version-control, .deleted-files {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.upload-section {
  margin-bottom: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 6px;
}

.upload-form {
  display: flex;
  gap: 10px;
  align-items: center;
}

.comment-input {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.version-table, .deleted-files-table {
  width: 100%;
  border-collapse: collapse;
}

.version-header, .deleted-file-header {
  display: grid;
  grid-template-columns: 80px 150px 100px 1fr 200px;
  padding: 10px;
  background: #f8f9fa;
  font-weight: bold;
  border-bottom: 2px solid #dee2e6;
}

.version-row, .deleted-file-row {
  display: grid;
  grid-template-columns: 80px 150px 100px 1fr 200px;
  padding: 10px;
  border-bottom: 1px solid #dee2e6;
  align-items: center;
}

.current-version {
  background: #e8f4ff;
}

.actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
  transition: background-color 0.2s;
}

.action-btn.restore {
  background: #28a745;
  color: white;
}

.action-btn.delete {
  background: #dc3545;
  color: white;
}

.action-btn:hover {
  opacity: 0.9;
}

.toggle-view-btn {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 20px;
}

.toggle-view-btn:hover {
  background: #0056b3;
}

.no-versions, .no-files {
  text-align: center;
  padding: 20px;
  color: #6c757d;
}

.version-comparison {
  margin-top: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 6px;
}

.comparison-result {
  background: #fff;
  padding: 15px;
  border-radius: 4px;
  border: 1px solid #dee2e6;
  overflow-x: auto;
}

pre {
  margin: 0;
  white-space: pre-wrap;
}

h2 {
  color: #2c3e50;
  margin-bottom: 20px;
}

h3 {
  color: #34495e;
  margin-bottom: 15px;
}
</style>
