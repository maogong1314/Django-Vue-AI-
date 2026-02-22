<script setup>
import { onMounted } from 'vue' 
import { RouterView } from 'vue-router' 
import { useAuthStore } from '@/stores/auth' 
import { fetchCsrfToken } from '@/services/api' 
import NavBar from './components/NavBar.vue'

const authStore = useAuthStore()


onMounted(() => {
  fetchCsrfToken().then(() => {
    authStore.checkAuth()
  })
})
</script>

<template>
  <header>
    <NavBar />
  </header>

  <main>
    <RouterView /> 
  </main>
</template>

<style scoped>
header {
  line-height: 1.5;
  max-height: 100vh;
}

main {
  padding: 2rem;
}
</style> 