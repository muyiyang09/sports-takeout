import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
    plugins: [vue()],
    server: {
        port: 5173,
        proxy: {
            // 将 /admin 前缀请求转发到后端，避免跨域
            '/admin': {
                target: 'http://localhost:8080',
                changeOrigin: true
            }
        }
    }
});
