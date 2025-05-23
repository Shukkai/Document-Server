import { createApp } from 'vue'
import App     from './App.vue'
import router  from './router'
import axios   from 'axios'

axios.defaults.baseURL         = '/api'      // nginx proxy → backend
axios.defaults.withCredentials = true        // send cookies everywhere

createApp(App).use(router).mount('#app')