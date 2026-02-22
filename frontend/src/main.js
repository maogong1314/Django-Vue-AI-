import './assets/main.css' // 导入全局样式

import { createApp } from 'vue' // 导入 Vue 创建应用的方法
import { createPinia } from 'pinia' // 导入 Pinia 状态管理

import App from './App.vue' // 导入根组件 App.vue
import router from './router' // 导入路由配置

const app = createApp(App) // 创建 Vue 应用实例

app.use(createPinia()) // 安装 Pinia 插件，实现全局状态管理
app.use(router) // 安装路由插件，实现页面导航

app.mount('#app') // 挂载应用到页面的 #app 根节点 