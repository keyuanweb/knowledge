import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)

// 全局状态管理
app.use(createPinia())

// 路由
app.use(router)

app.mount('#app')
