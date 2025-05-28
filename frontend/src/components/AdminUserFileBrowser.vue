<template>
  <div class="admin-user-file-browser">
    <h2>Admin: Browse User Files</h2>

    <!-- User Selection -->
    <div v-if="!selectedUser" class="user-selection-container">
      <div v-if="isLoadingUsers" class="loading-indicator">Loading users...</div>
      <div v-if="userError" class="error-message">{{ userError }}</div>
      <div v-if="!isLoadingUsers && !userError">
        <label for="user-select">Select a user to browse:</label>
        <select id="user-select" v-model="selectedUserId" @change="fetchUserFiles">
          <option disabled value="">Please select a user</option>
          <option v-for="userItem in users" :key="userItem.id" :value="userItem.id">
            {{ userItem.username }} ({{ userItem.email }})
          </option>
        </select>
      </div>
    </div>

    <!-- File Browser for Selected User -->
    <div v-if="selectedUser" class="selected-user-files">
      <div class="browser-header">
        <h3>
          Browsing files for: <strong>{{ selectedUser.username }}</strong>
        </h3>
        <button @click="resetUserSelection" class="change-user-btn">Change User</button>
      </div>
      
      <div v-if="isLoadingFiles" class="loading-indicator">Loading files for {{ selectedUser.username }}...</div>
      <div v-if="filesError" class="error-message">{{ filesError }}</div>

      <div v-if="userFileTree && !isLoadingFiles && !filesError" class="file-tree-container">
         <SimpleFolderTreeView 
            :treeData="[userFileTree]" 
            @show-versions="handleShowVersions"
          />
      </div>
       <div v-if="!userFileTree && !isLoadingFiles && !filesError && selectedUser" class="no-content-user">
          <p>No files or folders found for {{ selectedUser.username }}.</p>
      </div>
    </div>

    <!-- Version Control Modal (Reusing existing FileVersion component) -->
    <div v-if="fileForVersions" class="modal-overlay" @click="closeVersionModal">
      <div class="modal-content version-modal-content" @click.stop>
        <div class="modal-header">
          <h3>
            <span class="icon">📋</span>
            Version Control - {{ fileForVersions.name }}
             (User: {{ selectedUser.username }})
          </h3>
          <button class="modal-close" @click="closeVersionModal">×</button>
        </div>
        <div class="modal-body">
          <FileVersion 
            :fileId="fileForVersions.id"
            :isAdmin="true" 
            @success="handleVersionOpSuccess"
            @error="handleVersionOpError"
          />
        </div>
      </div>
    </div>
     <!-- Generic Success/Error Messages for Version Ops -->
    <div v-if="versionOpMessage" :class="['floating-message', versionOpError ? 'error' : 'success']">
      {{ versionOpMessage }}
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import SimpleFolderTreeView from './SimpleFolderTreeView.vue'; // Import the new tree view
import FileVersion from './FileVersion.vue'; // To show versions

const users = ref([]);
const selectedUserId = ref('');
const selectedUser = ref(null);
const userFileTree = ref(null);

const isLoadingUsers = ref(false);
const userError = ref(null);
const isLoadingFiles = ref(false);
const filesError = ref(null);

const fileForVersions = ref(null); // File object whose versions are to be shown
const versionOpMessage = ref(null);
const versionOpError = ref(false);

async function fetchUsersList() {
  isLoadingUsers.value = true;
  userError.value = null;
  users.value = [];
  try {
    const response = await axios.get('/admin/list-users');
    users.value = response.data;
  } catch (error) {
    console.error('Error fetching user list:', error);
    userError.value = 'Failed to load users. Ensure you are logged in as an admin.';
  } finally {
    isLoadingUsers.value = false;
  }
}

async function fetchUserFiles() {
  if (!selectedUserId.value) {
    userFileTree.value = null;
    selectedUser.value = null;
    return;
  }
  isLoadingFiles.value = true;
  filesError.value = null;
  userFileTree.value = null; 

  try {
    const response = await axios.get(`/admin/user-files/${selectedUserId.value}`);
    // The backend returns a single root folder object for the user in response.data.tree
    // SimpleFolderTreeView expects an array, or can handle a single root if structured like one.
    // We now pass response.data.tree directly if it has children (meaning it is the root folder obj)
    // or wrap it in an array if it doesn't (e.g. if root itself is empty or just has files).
    // The initial check `userFileTree.children ? [userFileTree] : userFileTree` in template handles this.
    userFileTree.value = response.data.tree;
    selectedUser.value = response.data.target_user;
    
    // Debug logging
    console.log('Admin API Response:', response.data);
    console.log('User File Tree:', userFileTree.value);
    console.log('Tree structure:', JSON.stringify(userFileTree.value, null, 2));
    
    if (!userFileTree.value || (userFileTree.value.children?.length === 0 && userFileTree.value.files?.length === 0 && userFileTree.value.id === null)) {
        // Backend returns a specific structure for empty root, handle it for display
        // This case is now better handled by SimpleFolderTreeView itself
    }
  } catch (error) {
    console.error(`Error fetching files for user ${selectedUserId.value}:`, error);
    filesError.value = `Failed to load files. ${error.response?.data?.error || 'Server error.'}`.trim();
  } finally {
    isLoadingFiles.value = false;
  }
}

function resetUserSelection() {
  selectedUserId.value = '';
  selectedUser.value = null;
  userFileTree.value = null;
  filesError.value = null;
  isLoadingFiles.value = false; // Reset loading state too
}

function handleShowVersions(file) {
  fileForVersions.value = file;
}

function closeVersionModal() {
  fileForVersions.value = null;
}

function handleVersionOpSuccess(message) {
  versionOpMessage.value = message || 'Version operation successful!';
  versionOpError.value = false;
  setTimeout(() => versionOpMessage.value = null, 3000);
  // Optionally, re-fetch user files if a version restore/delete might change display
  // fetchUserFiles(); // This might be too aggressive, depends on UX preference
  closeVersionModal(); // Close modal on success
}

function handleVersionOpError(message) {
  versionOpMessage.value = message || 'Version operation failed.';
  versionOpError.value = true;
  setTimeout(() => versionOpMessage.value = null, 5000);
  // Keep modal open on error for user to see context
}

onMounted(() => {
  fetchUsersList();
});

</script>

<style scoped>
.admin-user-file-browser {
  padding: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
}

.admin-user-file-browser h2 {
  color: #333;
  border-bottom: 2px solid #007bff;
  padding-bottom: 10px;
  margin-bottom: 20px;
}

.user-selection-container {
  margin-bottom: 1.5rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e9ecef;
  transition: all 0.2s ease;
}

.user-selection-container:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

.user-selection-container label {
  display: block;
  margin-bottom: 0.8rem;
  font-weight: 600;
  color: #2d3748;
  font-size: 1rem;
}

.user-selection-container select {
  width: 100%;
  padding: 0.8rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.95rem;
  background: white;
  transition: all 0.2s ease;
  cursor: pointer;
}

.user-selection-container select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.selected-user-files {
  margin-top: 0;
}

.browser-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.browser-header h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
}

.browser-header strong {
  color: #ffd700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.change-user-btn {
  padding: 0.6rem 1.2rem;
  font-size: 0.9rem;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
  font-weight: 500;
}

.change-user-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-1px);
}

.loading-indicator {
  margin: 2rem 0;
  color: #667eea;
  font-style: italic;
  text-align: center;
  padding: 2rem;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  border-radius: 12px;
  border: 2px dashed #667eea;
  font-weight: 500;
}

.error-message {
  margin: 1.5rem 0;
  color: #e53e3e;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #fed7d7, #feb2b2);
  border: 1px solid #fc8181;
  border-radius: 12px;
  border-left: 4px solid #e53e3e;
  box-shadow: 0 2px 8px rgba(229, 62, 62, 0.1);
}

.file-tree-container {
  margin-top: 0;
  padding: 1.5rem;
  background: #f8f9fa;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  min-height: 300px;
}

.no-content-user {
  padding: 3rem 2rem;
  text-align: center;
  color: #718096;
  background: linear-gradient(135deg, #f7fafc, #edf2f7);
  border: 2px dashed #cbd5e0;
  border-radius: 12px;
  margin-top: 1.5rem;
}

.no-content-user p {
  margin: 0;
  font-size: 1.1rem;
  color: #4a5568;
}

/* Modal styles */
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
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.version-modal-content {
  background: white;
  border-radius: 20px;
  width: 95%;
  max-width: 1400px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  padding: 2rem 2.5rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.5rem;
  color: white;
  font-weight: 600;
}

.modal-header .icon {
  margin-right: 0.8rem;
  font-size: 1.4rem;
}

.modal-close {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  font-size: 1.8rem;
  cursor: pointer;
  color: white;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: rotate(90deg);
}

.modal-body {
  padding: 2.5rem;
  overflow-y: auto;
  flex: 1;
}

.floating-message {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  padding: 1rem 2rem;
  border-radius: 12px;
  color: white;
  z-index: 2000;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(10px);
  font-weight: 500;
  animation: messageSlideUp 0.3s ease-out;
}

@keyframes messageSlideUp {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.floating-message.success {
  background: linear-gradient(135deg, #48bb78, #38a169);
}

.floating-message.error {
  background: linear-gradient(135deg, #f56565, #e53e3e);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .browser-header {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  .change-user-btn {
    align-self: stretch;
  }
  
  .file-tree-container {
    padding: 1rem;
  }
  
  .modal-body {
    padding: 1.5rem;
  }
  
  .version-modal-content {
    width: 95%;
    border-radius: 16px;
  }
}

@media (max-width: 480px) {
  .user-selection-container {
    padding: 1rem;
  }
  
  .browser-header {
    padding: 1rem;
  }
  
  .modal-header {
    padding: 1rem 1.5rem;
  }
  
  .modal-body {
    padding: 1rem;
  }
}
</style> 