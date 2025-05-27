import { createRouter, createWebHistory } from 'vue-router'
import axios from 'axios'
import { ref } from 'vue'

import LoginView           from '@/views/Login.vue'
import RegisterView        from '@/views/Register.vue'
import FilesView           from '@/views/Files.vue'
import ResetPasswordView   from '@/views/ResetPassword.vue'

/* -------- session cache ------------------ */
export const sessionCache = ref(null)  // null = unknown
export function setSession(val) {
  sessionCache.value = val
}

async function checkSession() {
  if (sessionCache.value !== null) return sessionCache.value
  
  try {
    // Simple health check to see if user is authenticated
    await axios.get('/folders', { 
      withCredentials: true,
      timeout: 5000
    })
    sessionCache.value = true
  } catch (error) {
    sessionCache.value = false
  }
  
  return sessionCache.value
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
    path: '/reset-password/:token', 
    name: 'ResetPassword', 
    component: ResetPasswordView 
  },
  { 
    path: '/login', 
    redirect: '/' 
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Global navigation guard
router.beforeEach(async (to, from, next) => {
  console.log('Navigating to:', to.path)
  
  // Allow access to public routes without session check
  if (to.path === '/' || to.path === '/register' || to.path.startsWith('/reset-password')) {
    return next()
  }
  
  const loggedIn = await checkSession()
  console.log('Session check result:', loggedIn)

  // Handle authentication for protected routes
  if (!loggedIn && to.path.startsWith('/files')) {
    console.log('Not logged in, redirecting to login')
    return next('/')
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