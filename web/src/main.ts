import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import Dashboard from './views/Dashboard.vue'
import ApiLogs from './views/ApiLogs.vue'
import IpBlacklist from './views/IpBlacklist.vue'
import Settings from './views/Settings.vue'
import ApiDoc from './views/ApiDoc.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Dashboard },
    { path: '/logs', component: ApiLogs },
    { path: '/blacklist', component: IpBlacklist },
    { path: '/settings', component: Settings },
    { path: '/api-doc', component: ApiDoc }
  ]
})

const app = createApp(App)
app.use(router)
app.use(ElementPlus)
app.mount('#app')
