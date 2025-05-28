<template>
  <nav class="main-nav">
    <router-link to="/">Home</router-link>
    <router-link v-if="isLoggedIn" to="/files">My Files</router-link> 
    <router-link v-if="isLoggedIn" to="/reviews">My Reviews</router-link>

    <!-- Admin Dashboard Link -->
    <div v-if="isAdmin" class="admin-nav-links">
      <router-link to="/admin-dashboard">Admin Dashboard</router-link>
    </div>
    
    <div class="user-actions">
      <router-link v-if="isLoggedIn" to="/user-info">User Info</router-link>
      <button v-if="isLoggedIn" @click="handleLogout" class="logout-btn">Logout</button>
      <router-link v-if="!isLoggedIn" to="/">Login</router-link>
    </div>
  </nav>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
// Import currentUser and sessionCache from your router/index.js
import { currentUser, sessionCache, setSession, forceSessionCheck } from '@/router/index.js'; 
import axios from 'axios';

const router = useRouter();

// Computed properties based on the globally managed currentUser and sessionCache
const isLoggedIn = computed(() => sessionCache.value === true && !!currentUser.value);
const isAdmin = computed(() => {
  const result = isLoggedIn.value && currentUser.value?.is_admin === true;
  console.log('Navbar isAdmin computed:', result, 'currentUser:', currentUser.value);
  return result;
});

// Force session refresh on mount to ensure we have latest user data
onMounted(async () => {
  if (sessionCache.value === true) {
    console.log('Navbar mounted - forcing session check');
    await forceSessionCheck();
  }
});

async function handleLogout() {
  try {
    await axios.post('/logout', {}, { withCredentials: true });
    setSession(false, null); // Update global state
    router.push('/'); // Redirect to login
  } catch (error) {
    console.error('Logout failed:', error);
    // Handle logout error, maybe show a message
  }
}

// No onMounted needed here for session status if router handles it initially
// and currentUser is kept up-to-date by router logic or auth service.

</script>

<style scoped>
.main-nav {
  display: flex;
  gap: 15px;
  padding: 10px 20px;
  background-color: #343a40; /* Darker background */
  align-items: center;
  color: white;
}

.main-nav a {
  color: #f8f9fa; /* Light text color */
  text-decoration: none;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.main-nav a:hover, .main-nav a.router-link-exact-active {
  background-color: #495057; /* Slightly lighter on hover/active */
  color: white;
}

.admin-nav-links a {
  font-weight: bold;
  color: #ffc107; /* Admin link yellow */
  border: 1px solid #ffc107;
}

.admin-nav-links a:hover {
  background-color: #e0a800;
  color: #212529;
}

.user-actions {
  margin-left: auto; /* Pushes user actions to the right */
  display: flex;
  align-items: center;
  gap: 15px;
}

.logout-btn {
  background-color: #dc3545;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: inherit; /* Match link font size */
}

.logout-btn:hover {
  background-color: #c82333;
}
</style> 