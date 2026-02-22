import axios from 'axios'; // 导入 axios，用于发送 HTTP 请求
import { sanitizePayload } from '@/utils/inputSanitizer';

// 这是一个辅助函数，用于从浏览器的cookie中获取指定名称的值。
// 我们用它来读取Django设置的 'csrftoken'。
export function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 后端地址：优先用环境变量，默认走相对路径 '/api'，便于 Vite 代理到本地 8000
const apiBase = import.meta?.env?.VITE_API_BASE || '/api';

// 我们创建一个Axios的"实例"，并对它进行预配置。
const apiClient = axios.create({
    baseURL: apiBase,           // 通过 Vite 代理可自动转发到后端
    withCredentials: true,      // 允许携带 cookie，用于认证/CSRF
});

// 使用"请求拦截器"，这是一个高级功能。
// 它会在我们每一次发送请求之前，先对请求进行一些处理。
apiClient.interceptors.request.use(config => {
    // 只对会改变服务器数据的请求方法（如POST）添加CSRF令牌
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(config.method.toUpperCase())) {
        const csrfToken = getCookie('csrftoken');
        if (csrfToken) {
            // 在请求头中添加 X-CSRFToken
            config.headers['X-CSRFToken'] = csrfToken;
        }
    }

    const requestPath = config.url || '';
    const isAuthRequest = requestPath.includes('/auth/') || requestPath.includes('/admin/register/');
    const isUploadRequest = requestPath.includes('/upload/');
    const shouldSanitize =
        ['POST', 'PUT', 'PATCH'].includes(config.method.toUpperCase()) && !isAuthRequest && !isUploadRequest;
    if (shouldSanitize) {
        config.data = sanitizePayload(config.data);
    }

    return config;
});

// 主动获取CSRF Token，确保浏览器有csrftoken cookie
export function fetchCsrfToken() {
    // 访问后端的安全GET接口，Django会自动发csrftoken cookie
    return apiClient.get('/auth/check/').catch(() => {});
}

// 模块加载时自动获取一次CSRF Token，防止首次操作缺失
fetchCsrfToken();

// 定义获取问题列表的函数
export const getQuestions = () => {
    return apiClient.get('/questions/');
};

// PATCH 修改对话（如重命名、置顶）
export const patchQuestion = (id, data) => {
    return apiClient.patch(`/questions/${id}/`, data);
};

// DELETE 删除对话
export const deleteQuestion = (id) => {
    return apiClient.delete(`/questions/${id}/`);
};

// 将我们配置好的实例导出，以便其他组件可以使用
export default apiClient; // 默认导出 