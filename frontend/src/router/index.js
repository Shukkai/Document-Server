import { createRouter, createWebHistory } from 'vue-router'
import axios from 'axios'
import { ref } from 'vue'

import LoginView           from '@/views/Login.vue'
import RegisterView        from '@/views/Register.vue'
import FilesView           from '@/views/Files.vue'
import ResetPasswordView   from '@/views/ResetPassword.vue'
import UserInfoView        from '@/views/UserInfo.vue'
import ReviewsView         from '@/views/Reviews.vue'
import AdminDashboard      from '../views/AdminDashboard.vue'

/* -------- session cache ------------------ */
export const sessionCache = ref(null)  // null = unknown
export const currentUser = ref(null)   // Current user information

export function setSession(val, user = null) {
  sessionCache.value = val
  currentUser.value = user
}

async function checkSession() {
  try {
    const response = await axios.get('/session-status', { 
      withCredentials: true,
      timeout: 5000
    })
    
    if (response.data.authenticated) {
      sessionCache.value = true
      currentUser.value = response.data.user
      return true
    } else {
      sessionCache.value = false
      currentUser.value = null
      return false
    }
  } catch (error) {
    console.error('Session check failed:', error)
    sessionCache.value = false
    currentUser.value = null
    return false
  }
}

// Force session check on page load/refresh
export async function forceSessionCheck() {
  return await checkSession()
}

// Periodic session monitor to detect session changes
let sessionCheckInterval = null

export function startSessionMonitoring() {
  if (sessionCheckInterval) return // Already running
  
  sessionCheckInterval = setInterval(async () => {
    const wasLoggedIn = sessionCache.value
    const wasUser = currentUser.value?.username
    
    const isLoggedIn = await checkSession()
    const currentUsername = currentUser.value?.username
    
    // Detect session conflicts
    if (wasLoggedIn && isLoggedIn && wasUser && currentUsername && wasUser !== currentUsername) {
      console.warn('Session conflict detected!', {
        was: wasUser,
        now: currentUsername
      })
      
      // Show warning to user
      if (window.confirm(`Session changed from ${wasUser} to ${currentUsername}. This may be due to another login in a different tab. Reload page?`)) {
        window.location.reload()
      }
    }
  }, 10000) // Check every 10 seconds
}

export function stopSessionMonitoring() {
  if (sessionCheckInterval) {
    clearInterval(sessionCheckInterval)
    sessionCheckInterval = null
  }
}
/* ----------------------------------------- */

const routes = [
  { 
    path: '/',               
    name: 'Login',          
    component: LoginView 
  },
  { 
    path: '/register',       
    name: 'Register',       
    component: RegisterView 
  },
  { 
    path: '/files',          
    name: 'Files',          
    component: FilesView
  },
  { 
    path: '/reviews',
    name: 'Reviews',
    component: ReviewsView
  },
  { 
    path: '/user-info',
    name: 'UserInfo',
    component: UserInfoView
  },
  { 
    path: '/reset-password/:token', 
    name: 'ResetPassword', 
    component: ResetPasswordView 
  },
  { 
    path: '/login', 
    redirect: '/' 
  },
  {
    path: '/admin-dashboard',
    name: 'AdminDashboard',
    component: AdminDashboard,
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Global navigation guard
router.beforeEach(async (to, from, next) => {
  console.log('Navigating to:', to.path, 'Current user:', currentUser.value?.username, 'Is admin:', currentUser.value?.is_admin)
  
  // Allow access to public routes without session check
  if (to.path === '/' || to.path === '/register' || to.path.startsWith('/reset-password')) {
    return next()
  }
  
  // Always check session for protected routes (don't use cache)
  const loggedIn = await checkSession()
  console.log('Session check result:', loggedIn, 'User:', currentUser.value?.username, 'Is admin:', currentUser.value?.is_admin)

  // Handle authentication for protected routes
  if (!loggedIn && (to.path.startsWith('/files') || to.path === '/user-info' || to.path === '/reviews' || to.path === '/admin-dashboard')) {
    console.log('Not logged in, redirecting to login')
    return next('/')
  }
  
  // Check admin access for admin routes
  if (to.meta?.requiresAdmin && (!loggedIn || !currentUser.value?.is_admin)) {
    console.log('Admin access required but user is not admin, redirecting to files')
    return next('/files')
  }
  
  // If logged in and trying to access login, redirect to files
  if (loggedIn && (to.path === '/' || to.path === '/login')) {
    console.log('Already logged in, redirecting to files')
    return next('/files')
  }

  next()
})

// Global error handler
router.onError((error) => {
  console.error('Router error:', error)
})

export default router