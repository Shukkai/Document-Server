<template>
    <div class="reset-container">
      <h2>Reset Password</h2>
      <form @submit.prevent="resetPassword">
        <div class="field">
          <label for="password">New Password</label>
          <input id="password" v-model="password" type="password" required />
        </div>
        <button type="submit">Submit</button>
        <p v-if="message" class="msg">{{ message }}</p>
      </form>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  import axios from 'axios'
  import { useRoute, useRouter } from 'vue-router'
  
  const route = useRoute()
  const router = useRouter()
  const password = ref('')
  const message = ref('')
  
  async function resetPassword() {
    try {
      await axios.post(`/reset-password/${route.params.token}`, { password: password.value })
      message.value = 'Password reset successfully. Redirecting...'
      setTimeout(() => router.push('/'), 2000)
    } catch (err) {
      message.value = err.response?.data?.error || 'Reset failed.'
    }
  }
  </script>
  
  <style scoped>
  .reset-container { max-width:400px; margin:3rem auto; padding:2rem; box-shadow:0 0 8px #0001; background:#fff; border-radius:8px }
  .field { margin-bottom:1rem }
  .field label { display:block; margin-bottom:.25rem; font-weight:600 }
  .field input { width:100%; padding:.5rem; border:1px solid #ccc; border-radius:4px }
  button { padding:.6rem; background:#3f51b5; color:#fff; border:none; border-radius:4px; cursor:pointer }
  .msg { margin-top:1rem; color:green }
  </style>