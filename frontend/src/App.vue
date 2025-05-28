<template>
  <div class="app">
    <header class="navbar">
      <h1>📁 Cloud Document Center</h1>
      <div v-if="isLoggedIn" class="header-right">
        <div class="user-indicator">
          <span class="user-icon">👤</span>
          <span class="username">{{ currentUser?.username }}</span>
          <span v-if="currentUser?.is_admin" class="admin-badge">ADMIN</span>
        </div>
        <NotificationBar />
      </div>
    </header>
    <main class="main-content">
      <router-view />                   <!-- all pages render here -->
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { sessionCache, currentUser, startSessionMonitoring, stopSessionMonitoring } from '@/router'
import NotificationBar from '@/components/NotificationBar.vue'

const isLoggedIn = computed(() => sessionCache.value === true)

onMounted(() => {
  // Start global session monitoring when app loads
  if (isLoggedIn.value) {
    startSessionMonitoring()
  }
})

onUnmounted(() => {
  stopSessionMonitoring()
})
</script>

<style>
body { margin:0; font-family:Arial, sans-serif; background:#f9f9f9; }
.app { display:flex; flex-direction:column; min-height:100vh; }
.navbar { 
  background:#3f51b5; 
  color:#fff; 
  padding:1rem; 
  display: flex; 
  align-items: center; 
  justify-content: space-between;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.user-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
}
.user-icon {
  font-size: 1.2rem;
}
.username {
  font-weight: 500;
}
.admin-badge {
  background: #ff5722;
  color: white;
  padding: 0.1rem 0.5rem;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: bold;
}
.main-content { flex:1; padding:2rem; }
</style>