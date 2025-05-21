<template>
  <div class="app">
    <header class="navbar">
      <h1>📁 Cloud Document Center</h1>
    </header>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
// No global logic yet
</script>

<style>
body {
  margin: 0;
  font-family: Arial, sans-serif;
  background-color: #f9f9f9;
}

.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.navbar {
  background-color: #3f51b5;
  color: white;
  padding: 1rem;
  text-align: center;
}

.main-content {
  flex: 1;
  padding: 2rem;
}
</style>