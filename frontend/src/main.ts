import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { signIn } from './services/firebase.js'

const app = createApp(App)

app.use(createPinia())
app.use(router)

// By calling signIn here and putting app.mount() in the .then() block,
// we ensure that the user is authenticated *before* the app is rendered.
signIn().then(() => {
  app.mount('#app')
})
