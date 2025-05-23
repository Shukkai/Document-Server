import { createRouter, createWebHistory } from 'vue-router'
import axios from 'axios'
import { ref } from 'vue'

import LoginView    from '@/views/Login.vue'
import RegisterView from '@/views/Register.vue'
import FilesView    from '@/views/Files.vue'
import ResetPasswordView from '@/views/ResetPassword.vue'

/* -------- simple in‑memory session cache ------------------ */
export const sessionCache = ref(null)          // null = unknown
export function setSession (val) { sessionCache.value = val }

async function checkSession () {
  if (sessionCache.value !== null) return sessionCache.value
  sessionCache.value = await axios
    .get('/files', { validateStatus: s => s < 400 })
    .then(() => true)
    .catch(() => false)
  return sessionCache.value
}
/* ----------------------------------------------------------- */

const routes = [
  { path: '/',          name:'Login',    component: LoginView },
  { path: '/register',  name:'Register', component: RegisterView },
  { path: '/files',     name:'Files',    component: FilesView },
  { path: '/reset-password/:token', name: 'ResetPassword', component: ResetPasswordView },
  { path: '/login', redirect:'/' }     // alias
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to, from, next) => {
  const logged = await checkSession()

  if (!logged && to.path === '/files')  return next('/')   // protect files
  if ( logged && (to.path === '/' || to.path === '/login')) return next('/files')
  next()
})

export default router