import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';

// 后端地址通过 .env.development / .env.production 的 VITE_API_BASE 分层（§5.25）
export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), '');

    return {
        plugins: [vue()],
        server: {
            port: 5173,
            proxy: {
                // 将 /admin 前缀请求转发到后端，避免跨域
                '/admin': {
                    target: env.VITE_API_BASE || 'http://localhost:8080',
                    changeOrigin: true
                }
            }
        }
    };
});
