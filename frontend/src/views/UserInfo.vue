<template>
  <div class="user-info-container">
    <div class="user-info-card">
      <h2>User Information</h2>
      
      <div v-if="loading" class="loading">
        <span class="icon">⏳</span> Loading user information...
      </div>
      
      <div v-else-if="userInfo" class="user-info-content">
        <div class="info-group">
          <div class="info-item">
            <label>Username:</label>
            <span class="value">{{ userInfo.username }}</span>
          </div>
          
          <div class="info-item">
            <label>Email:</label>
            <span class="value">{{ userInfo.email }}</span>
          </div>
          
          <div class="info-item">
            <label>Grade:</label>
            <span class="value">{{ userInfo.grade }}</span>
          </div>
          
          <div class="info-item">
            <label>Admin Status:</label>
            <span class="value admin-badge" :class="{ admin: userInfo.is_admin, regular: !userInfo.is_admin }">
              {{ userInfo.is_admin ? 'Administrator' : 'Regular User' }}
            </span>
          </div>
          
          <div class="info-item">
            <label>Member Since:</label>
            <span class="value">{{ formatDate(userInfo.created_at) }}</span>
          </div>
        </div>
      </div>
      
      <div v-if="errorMessage" class="error-message">
        ⚠️ {{ errorMessage }}
      </div>
      
      <div class="actions">
        <button class="btn secondary" @click="goBack">
          <span class="icon">⬅️</span> Back to Files
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const userInfo = ref(null)
const loading = ref(true)
const errorMessage = ref('')

onMounted(async () => {
  await loadUserInfo()
})

async function loadUserInfo() {
  loading.value = true
  errorMessage.value = ''
  
  try {
    const { data } = await axios.get('/user-info', { withCredentials: true })
    userInfo.value = data
  } catch (err) {
    console.error('Error loading user info:', err)
    errorMessage.value = err.response?.data?.error || 'Failed to load user information'
  } finally {
    loading.value = false
  }
}

function formatDate(dateString) {
  if (!dateString) return 'Unknown'
  
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  } catch (error) {
    return 'Invalid date'
  }
}

function goBack() {
  router.push('/files')
}
</script>

<style scoped>
.user-info-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.user-info-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
  padding: 2rem;
  width: 100%;
  max-width: 500px;
}

.user-info-card h2 {
  text-align: center;
  color: #333;
  margin-bottom: 2rem;
  font-weight: 600;
}

.loading {
  text-align: center;
  color: #666;
  padding: 2rem;
}

.user-info-content {
  margin-bottom: 2rem;
}

.info-group {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.info-item label {
  font-weight: 600;
  color: #555;
  min-width: 120px;
}

.info-item .value {
  font-weight: 500;
  color: #333;
  text-align: right;
}

.admin-badge {
  padding: 0.3rem 0.8rem;
  border-radius: 16px;
  font-size: 0.85rem;
  font-weight: 600;
}

.admin-badge.admin {
  background: #e8f5e8;
  color: #2e7d32;
  border: 1px solid #4caf50;
}

.admin-badge.regular {
  background: #f3f4f6;
  color: #6b7280;
  border: 1px solid #d1d5db;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  border-left: 4px solid #f44336;
}

.actions {
  text-align: center;
}

.btn {
  padding: 0.8rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn.secondary {
  background: #6c757d;
  color: white;
}

.btn.secondary:hover {
  background: #5a6268;
  transform: translateY(-2px);
}

.icon {
  font-size: 1.1em;
}

@media (max-width: 768px) {
  .user-info-container {
    padding: 10px;
  }
  
  .user-info-card {
    padding: 1.5rem;
  }
  
  .info-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .info-item .value {
    text-align: left;
  }
}
</style> 