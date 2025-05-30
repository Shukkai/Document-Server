<template>
  <v-container class="d-flex align-center justify-center" style="height:100vh">
    <v-progress-circular indeterminate size="64" width="6" />
  </v-container>
</template>

<script setup>
import axios from 'axios'
import { onMounted }  from 'vue'
import { useRouter }  from 'vue-router'
import { setSession } from '../router'

const router   = useRouter()

onMounted(async () => {
  try {
    const response = await axios.get(
      '/session-status',
      { withCredentials: true }
    )
    setSession(true, response.data.user) // Set session with user information
    console.log('Logged in as:', response.data.user.username)
    router.replace('/files')
  } catch (err) {
    console.error('OAuth success handler failed', err)
    // fallback – go back to login
    router.replace('/login')
  }
})
</script>
