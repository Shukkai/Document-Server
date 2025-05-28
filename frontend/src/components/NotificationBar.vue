<template>
  <div class="notification-bar">
    <div class="notification-icon" @click="toggleDropdown" :class="{ active: showDropdown }">
      <span class="icon">🔔</span>
      <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
    </div>

    <div v-if="showDropdown" class="notification-dropdown" @click.stop>
      <div class="dropdown-header">
        <h3>Notifications</h3>
        <button v-if="unreadCount > 0" @click="markAllRead" class="mark-all-btn">
          Mark all read
        </button>
      </div>

      <div class="notification-list">
        <div v-if="notifications.length === 0" class="no-notifications">
          No notifications
        </div>
        
        <div 
          v-for="notification in notifications" 
          :key="notification.id"
          class="notification-item"
          :class="{ unread: !notification.is_read }"
          @click="handleNotificationClick(notification)"
        >
          <div class="notification-content">
            <h4>{{ notification.title }}</h4>
            <p>{{ notification.message }}</p>
            <small>{{ formatDate(notification.created_at) }}</small>
          </div>
          <button 
            v-if="!notification.is_read" 
            @click.stop="markAsRead(notification.id)"
            class="mark-read-btn"
          >
            ✓
          </button>
        </div>
      </div>

      <div class="dropdown-footer">
        <router-link to="/reviews" class="btn btn-sm">View My Reviews</router-link>
      </div>
    </div>

    <!-- Overlay to close dropdown when clicking outside -->
    <div v-if="showDropdown" class="overlay" @click="closeDropdown"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const notifications = ref([])
const showDropdown = ref(false)

const unreadCount = computed(() => 
  notifications.value.filter(n => !n.is_read).length
)

async function fetchNotifications() {
  try {
    const response = await axios.get('/notifications', { withCredentials: true })
    notifications.value = response.data
  } catch (error) {
    console.error('Error fetching notifications:', error)
  }
}

async function markAsRead(notificationId) {
  try {
    await axios.post(`/notifications/${notificationId}/read`, {}, { withCredentials: true })
    // Update local state
    const notification = notifications.value.find(n => n.id === notificationId)
    if (notification) {
      notification.is_read = true
    }
  } catch (error) {
    console.error('Error marking notification as read:', error)
  }
}

async function markAllRead() {
  try {
    await axios.post('/notifications/mark-all-read', {}, { withCredentials: true })
    // Update local state
    notifications.value.forEach(n => n.is_read = true)
  } catch (error) {
    console.error('Error marking all notifications as read:', error)
  }
}

function toggleDropdown() {
  showDropdown.value = !showDropdown.value
}

function closeDropdown() {
  showDropdown.value = false
}

function handleNotificationClick(notification) {
  // Mark as read if not already
  if (!notification.is_read) {
    markAsRead(notification.id)
  }

  // Navigate based on notification type
  if (notification.type === 'review_request' && notification.related_file_id) {
    router.push('/reviews')
  } else if (notification.related_file_id) {
    router.push('/files')
  }
  
  closeDropdown()
}

function formatDate(dateString) {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  
  // Less than 1 minute
  if (diff < 60000) {
    return 'Just now'
  }
  
  // Less than 1 hour
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000)
    return `${minutes} minute${minutes > 1 ? 's' : ''} ago`
  }
  
  // Less than 1 day
  if (diff < 86400000) {
    const hours = Math.floor(diff / 3600000)
    return `${hours} hour${hours > 1 ? 's' : ''} ago`
  }
  
  // More than 1 day
  return date.toLocaleDateString()
}

// Fetch notifications on mount and set up polling
onMounted(() => {
  fetchNotifications()
  
  // Poll for new notifications every 30 seconds
  setInterval(fetchNotifications, 30000)
})
</script>

<style scoped>
.notification-bar {
  position: relative;
  margin-left: auto;
}

.notification-icon {
  position: relative;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  transition: background-color 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notification-icon:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.notification-icon.active {
  background-color: rgba(255, 255, 255, 0.2);
}

.icon {
  font-size: 1.5rem;
}

.badge {
  position: absolute;
  top: 0;
  right: 0;
  background: #e53e3e;
  color: white;
  border-radius: 50%;
  width: 1.2rem;
  height: 1.2rem;
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.notification-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  width: 350px;
  max-width: 90vw;
  max-height: 400px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
  z-index: 1150;
  overflow: hidden;
}

/* Responsive positioning for smaller screens */
@media (max-width: 480px) {
  .notification-dropdown {
    right: -1rem;
    width: 320px;
    max-width: calc(100vw - 2rem);
  }
}

.dropdown-header {
  padding: 1rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8fafc;
}

.dropdown-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #2d3748;
}

.mark-all-btn {
  background: none;
  border: none;
  color: #4299e1;
  font-size: 0.8rem;
  cursor: pointer;
  font-weight: 500;
}

.mark-all-btn:hover {
  text-decoration: underline;
}

.notification-list {
  max-height: 300px;
  overflow-y: auto;
}

.no-notifications {
  padding: 2rem;
  text-align: center;
  color: #718096;
  font-style: italic;
}

.notification-item {
  padding: 1rem;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  transition: background-color 0.2s ease;
}

.notification-item:hover {
  background: #f8fafc;
}

.notification-item.unread {
  background: #edf2f7;
  border-left: 3px solid #4299e1;
}

.notification-content {
  flex: 1;
}

.notification-content h4 {
  margin: 0 0 0.25rem 0;
  font-size: 0.9rem;
  color: #2d3748;
  font-weight: 600;
}

.notification-content p {
  margin: 0 0 0.5rem 0;
  font-size: 0.85rem;
  color: #4a5568;
  line-height: 1.4;
}

.notification-content small {
  color: #718096;
  font-size: 0.75rem;
}

.mark-read-btn {
  background: #4299e1;
  color: white;
  border: none;
  border-radius: 50%;
  width: 1.5rem;
  height: 1.5rem;
  font-size: 0.8rem;
  cursor: pointer;
  flex-shrink: 0;
}

.mark-read-btn:hover {
  background: #3182ce;
}

.dropdown-footer {
  padding: 0.75rem;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
  text-align: center;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  transition: background-color 0.2s ease;
}

.btn.btn-sm {
  background: #4299e1;
  color: white;
}

.btn.btn-sm:hover {
  background: #3182ce;
}

.overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1149;
}
</style> 