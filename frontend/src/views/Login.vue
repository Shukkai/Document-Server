<template>
  <div class="login-container">
    <h2>Login</h2>

    <form @submit.prevent="handleLogin">
      <div class="field">
        <label for="username">Username</label>
        <input id="username" v-model="username" type="text" required />
      </div>

      <div class="field">
        <label for="password">Password</label>
        <input id="password" v-model="password" type="password" required />
      </div>

      <button type="submit">Login</button>

      <button
        type="button"
        @click="loginWithGoogle"
      >使用 Google 進行登入</button>

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </form>

    <p class="switch">
      Don't have an account? <router-link to="/register">Register here</router-link>
    </p>
    <p class="reset-link">
      Forgot password? <a href="#" @click.prevent="promptReset">Reset</a>
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { setSession } from '@/router'

const username = ref('')
const password = ref('')
const errorMessage = ref('')
const router = useRouter()

function loginWithGoogle () {
  window.location.href = "/api/auth/google/login"
}

async function handleLogin () {
  errorMessage.value = ''
  try {
    const response = await axios.post('/login', {
      username: username.value,
      password: password.value
    }, { withCredentials: true })
    
    // Set session with user information
    setSession(true, response.data.user)
    console.log('Logged in as:', response.data.user.username)
    router.push('/files')
  } catch (error) {
    console.error('Login failed:', error)
    errorMessage.value = error.response?.data?.error || 'Login failed.'
  }
}

async function promptReset () {
  const email = prompt('Enter your registered email:')
  if (!email) return
  try {
    await axios.post('/request-reset', { email })
    alert('If the email exists, a reset link has been sent.')
  } catch {
    alert('Something went wrong. Please try again.')
  }
}

// onMounted(() => {
//   console.log('Login component mounted')
// })
</script>

<style scoped>
.login-container { max-width:400px; margin:3rem auto; padding:2rem; box-shadow:0 0 8px #0001; background:#fff; border-radius:8px; }
.field { margin-bottom:1rem }
.field label { display:block; margin-bottom:.25rem; font-weight:600 }
.field input { width:100%; padding:.5rem .75rem; border:1px solid #ccc; border-radius:4px }
button { width:100%; padding:.6rem; background:#3f51b5; color:#fff; border:none; border-radius:4px; cursor:pointer; margin-bottom: 1rem }
button:hover { background:#3344a3 }
.error { color:#e53935; margin-top:.75rem }
.switch, .reset-link { margin-top:1rem; text-align:center }
.reset-link a { color: #3f51b5; text-decoration: underline; cursor: pointer }
</style>