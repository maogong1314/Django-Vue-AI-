import { createRouter, createWebHistory } from 'vue-router' // 导入 Vue Router 的核心方法
import QuestionListView from '../views/QuestionListView.vue' // 导入问题列表页面组件
import LoginView from '../views/LoginView.vue' // 导入登录页面组件
import RegisterView from '../views/RegisterView.vue' // 导入注册页面组件
import AdminLoginView from '../views/AdminLoginView.vue' // 导入管理员登录页面组件
import AdminDashboard from '../views/AdminDashboard.vue' // 导入管理员后台页面组件
import NovelManager from '../views/NovelManager.vue' // 导入小说管理页面组件
import NovelReader from '../views/NovelReader.vue' // 导入小说阅读页面组件
import NovelWorkspace from '../views/NovelWorkspace.vue' // 导入小说工作区页面组件
import NovelSpider from '../views/NovelSpider.vue' // 导入小说爬虫页面组件
import { useAuthStore } from '@/stores/auth' // 导入 Pinia 的用户认证状态管理

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL), // 使用 HTML5 history 模式，BASE_URL 为基础路径
  routes: [
    {
      path: '/',
      name: 'home',
      component: QuestionListView // 首页，显示问题列表
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('../views/ChatView.vue') // 聊天页面，懒加载
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView // 登录页面
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView // 注册页面
    },
    { path: '/admin-login', name: 'admin-login', component: AdminLoginView }, // 管理员登录
    { path: '/admin', name: 'admin', component: AdminDashboard }, // 管理员后台
    { path: '/novel', name: 'novel', component: NovelManager }, // 小说管理
    { path: '/novel-reader', name: 'novel-reader', component: NovelReader }, // 小说阅读
    { path: '/novel-workspace', name: 'novel-workspace', component: NovelWorkspace }, // 小说工作区
    { path: '/novel-spider', name: 'novel-spider', component: NovelSpider }, // 小说爬虫
    { path: '/novel-home', name: 'novel-home', component: () => import('../views/NovelFront.vue') }, 
   
  ]
})

// 路由导航守卫：用于控制页面访问权限
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore() // 获取认证状态
  const publicPages = ['/login', '/register', '/admin-login']; // 公共页面路径
  const authRequired = !publicPages.includes(to.path); // 判断目标页面是否需要认证

  // 如果需要认证且未认证，尝试检查认证状态
  if (authRequired && !authStore.isAuthenticated) {
    await authStore.checkAuth()
  }

  // 如果需要认证且未登录，跳转到登录页
  if (authRequired && !authStore.isAuthenticated) {
    return next('/login');
  }

  next(); // 允许路由跳转
})

export default router // 导出路由实例，供 main.js 挂载 