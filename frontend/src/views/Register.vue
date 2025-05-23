<template>
    <div class="register-container">
      <h2>Create an account</h2>
  
      <form @submit.prevent="handleRegister">
        <div class="field">
          <label>Username</label>
          <input v-model="username" type="text" required />
        </div>
  
        <div class="field">
          <label>Email</label>
          <input v-model="email" type="email" required />
        </div>
  
        <div class="field">
          <label>Password</label>
          <input v-model="password" type="password" required />
        </div>
  
        <button type="submit">Register</button>
        <p v-if="errorMessage"  class="error">{{ errorMessage }}</p>
        <p v-if="successMessage" class="success">{{ successMessage }}</p>
      </form>
  
      <p class="switch">
        Already have an account? <router-link to="/">Login here</router-link>
      </p>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  import axios     from 'axios'
  import { useRouter } from 'vue-router'
  
  const username       = ref('')
  const email          = ref('')
  const password       = ref('')
  const errorMessage   = ref('')
  const successMessage = ref('')
  const router         = useRouter()
  
  async function handleRegister () {
    errorMessage.value = successMessage.value = ''
    try {
      await axios.post('/register', { username: username.value, email: email.value, password: password.value })
      successMessage.value = 'Registered! Redirecting…'
      setTimeout(() => router.push('/'), 1200)
    } catch (err) {
      errorMessage.value = err.response?.data?.error || 'Registration failed.'
    }
  }
  </script>
  
  <style scoped>
  /* same style block as Login with .success { color:#43a047 } */
  </style>