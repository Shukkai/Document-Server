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
    // Check both folders and version endpoints to ensure full access
    await Promise.all([
      axios.get('/folders', { validateStatus: s => s < 400 }),
      axios.get('/file-versions', { validateStatus: s => s < 400 })
    ])
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
    component: FilesView,
    props: route => ({ 
      folderId: route.query.folder,
      versionId: route.query.version 
    })
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
  // Catch all route for 404s
  {
    path: '/:pathMatch(.*)*',
    redirect: '/files'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Global navigation guard
router.beforeEach(async (to, from, next) => {
  const loggedIn = await checkSession()

  // Handle authentication
  if (!loggedIn && to.path.startsWith('/files')) {
    return next('/')
  }
  if (loggedIn && (to.path === '/' || to.path === '/login')) {
    return next('/files')
  }

  // Handle version-specific routes
  if (to.path.startsWith('/files') && to.query.version) {
    // Ensure user has access to the version
    try {
      await axios.get(`/file-versions/${to.query.version}`, { 
        validateStatus: s => s < 400 
      })
    } catch (error) {
      // If version access fails, redirect to files without version
      const { version, ...query } = to.query
      return next({ path: '/files', query })
    }
  }

  next()
})

// Global error handler
router.onError((error) => {
  console.error('Router error:', error)
  // Redirect to files page on error
  router.push('/files')
})

export default router