<template>
    <div>
      <h1>Document Center</h1>
      <input type="file" @change="onFileChange" />
      <button @click="upload">Upload</button>
  
      <ul>
        <li v-for="file in files" :key="file.id">
          {{ file.name }}
          <a :href="`http://localhost:5001/download/${file.id}`" target="_blank">Download</a>
        </li>
      </ul>
    </div>
  </template>
  
  <script>
  import axios from 'axios'
  
  export default {
    data() {
      return {
        selectedFile: null,
        files: []
      }
    },
    methods: {
      onFileChange(event) {
        this.selectedFile = event.target.files[0]
      },
      async upload() {
        const formData = new FormData()
        formData.append('file', this.selectedFile)
        await axios.post('http://localhost:5001/upload', formData)
        this.loadFiles()
      },
      async loadFiles() {
        const res = await axios.get('http://localhost:5001/files')
        this.files = res.data
      }
    },
    mounted() {
      this.loadFiles()
    }
  }
  </script>