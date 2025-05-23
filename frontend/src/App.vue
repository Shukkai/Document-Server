<template>
  <div class="app">
    <header class="navbar">
      <h1>📁 Cloud Document Center</h1>
    </header>
    <main class="main-content">
      <router-view />                   <!-- all pages render here -->
    </main>
  </div>
</template>

<script setup></script>

<style>
body { margin:0; font-family:Arial, sans-serif; background:#f9f9f9; }
.app { display:flex; flex-direction:column; min-height:100vh; }
.navbar { background:#3f51b5; color:#fff; padding:1rem; text-align:center; }
.main-content { flex:1; padding:2rem; }
</style>