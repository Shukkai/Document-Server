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
        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      </form>
  
      <p class="switch">
        Don’t have an account? <router-link to="/register">Register here</router-link>
      </p>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  import axios     from 'axios'
  import { useRouter } from 'vue-router'
  import { setSession } from '@/router'
  
  const username = ref('')
  const password = ref('')
  const errorMessage = ref('')
  const router = useRouter()
  
  async function handleLogin () {
    errorMessage.value = ''
    try {
      await axios.post('/login', { username: username.value, password: password.value })
      setSession(true)          // update cache
      router.push('/files')
    } catch {
      errorMessage.value = 'Login failed.'
    }
  }
  </script>
  
  <style scoped>
  .login-container { max-width:400px; margin:3rem auto; padding:2rem; box-shadow:0 0 8px #0001; background:#fff; border-radius:8px; }
  .field { margin-bottom:1rem }
  .field label { display:block; margin-bottom:.25rem; font-weight:600 }
  .field input { width:100%; padding:.5rem .75rem; border:1px solid #ccc; border-radius:4px }
  button { width:100%; padding:.6rem; background:#3f51b5; color:#fff; border:none; border-radius:4px; cursor:pointer }
  button:hover { background:#3344a3 }
  .error { color:#e53935; margin-top:.75rem }
  .switch { margin-top:1rem; text-align:center }
  </style>