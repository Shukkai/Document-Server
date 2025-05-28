<template>
  <div class="admin-dashboard">
    <!-- Header Section -->
    <div class="dashboard-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="dashboard-title">
            <span class="crown-icon">👑</span>
            Admin Dashboard
          </h1>
          <p class="dashboard-subtitle">Manage users and oversee system-wide file operations</p>
        </div>
        <div class="header-actions">
          <button @click="goToMainPage" class="action-btn main-page-btn">
            <span class="btn-icon">🏠</span>
            Go to Main Page
          </button>
          <div class="admin-badge">
            <span class="badge-icon">🛡️</span>
            <span class="badge-text">Administrator</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="dashboard-content">
      <!-- User File Browser Card -->
      <div class="admin-card full-width-card">
        <div class="card-header">
          <div class="card-title">
            <span class="card-icon">👥</span>
            <h2>User File Manager</h2>
          </div>
          <div class="card-description">
            Browse and manage files across all user accounts
          </div>
        </div>
        
        <div class="card-content">
          <AdminUserFileBrowser v-if="isAdminUser" />
          <div v-else class="access-denied">
            <div class="denied-icon">🚫</div>
            <p>Access Denied</p>
            <span>Administrator privileges required to view this section</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import AdminUserFileBrowser from '../components/AdminUserFileBrowser.vue';

const isAdminUser = ref(false);
const router = useRouter();

// Fetch admin status
onMounted(async () => {
  try {
    const response = await axios.get('/session-status');
    if (response.data && response.data.authenticated && response.data.user) {
      isAdminUser.value = !!response.data.user.is_admin;
    } else {
      isAdminUser.value = false;
    }
  } catch (error) {
    console.error('Error fetching admin status:', error);
    isAdminUser.value = false;
  }
});

// Method to navigate to the main page
function goToMainPage() {
  router.push('/files');
}
</script>

<style scoped>
.admin-dashboard {
  min-height: 100vh;
  background: #f0f2f5; /* Lighter, simpler background */
  padding: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.dashboard-header {
  background: #ffffff; /* White header */
  border-bottom: 1px solid #e8e8e8;
  padding: 1.5rem 0; /* Reduced padding */
  margin-bottom: 2rem;
}

.header-content {
  max-width: 1400px; /* Increased max-width for wider feel */
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section {
  color: #2c3e50; /* Darker text for better contrast */
}

.dashboard-title {
  margin: 0;
  font-size: 2rem; /* Slightly reduced title size */
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.crown-icon {
  font-size: 2rem;
  color: #667eea; /* Simpler color for crown */
  filter: none;
}

.dashboard-subtitle {
  margin: 0.3rem 0 0 0;
  font-size: 1rem;
  color: #596780;
  font-weight: 400;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1.2rem;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #fff;
  color: #2c3e50;
}

.action-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.btn-icon {
  font-size: 1rem;
}

.main-page-btn {
  /* Specific styles if needed, otherwise inherits from .action-btn */
}

.admin-badge {
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 16px; /* Simpler border radius */
  padding: 0.6rem 1.2rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #1890ff;
  font-weight: 500;
}

.badge-icon {
  font-size: 1rem;
}

.dashboard-content {
  max-width: 1400px; /* Increased max-width */
  margin: 0 auto;
  padding: 0 2rem 2rem;
}

.admin-card {
  background: white;
  border-radius: 12px; /* Simpler border radius */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); /* Softer shadow */
  overflow: hidden;
  transition: box-shadow 0.3s ease;
}

.admin-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.full-width-card {
  width: 100%; /* Ensure it takes full width of its container */
}

.card-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #f0f0f0;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.25rem;
}

.card-title h2 {
  margin: 0;
  color: #2c3e50;
  font-weight: 600;
  font-size: 1.3rem;
}

.card-icon {
  font-size: 1.3rem;
  padding: 0.5rem;
  background: #e6f7ff;
  color: #1890ff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-description {
  color: #596780;
  font-size: 0.9rem;
  margin: 0;
}

.card-content {
  padding: 2rem; /* Consistent padding */
}

.access-denied {
  text-align: center;
  padding: 3rem 1rem;
  color: #596780;
}

.denied-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  color: #ff4d4f;
}

/* Responsive Design */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    text-align: center;
    gap: 1.5rem; /* Increased gap for better separation */
  }
  
  .header-actions {
    flex-direction: column;
    gap: 0.8rem;
  }
  
  .dashboard-title {
    font-size: 1.8rem;
  }
  
  .admin-card {
    grid-row: span 1;
  }
}

@media (max-width: 480px) {
  .dashboard-content {
    padding: 0 1rem 1rem;
  }
  
  .card-header,
  .card-content {
    padding: 1.5rem;
  }
}
</style> 