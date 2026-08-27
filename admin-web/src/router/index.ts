import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';

// vue-router history 模式（§5.22），nginx 已配 try_files；路由守卫统一鉴权
const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/login',
            name: 'login',
            component: () => import('../views/LoginView.vue')
        },
        {
            path: '/',
            component: () => import('../layouts/AdminLayout.vue'),
            redirect: '/coach',
            children: [
                { path: 'coach', name: 'coach', component: () => import('../views/CoachView.vue') },
                { path: 'course', name: 'course', component: () => import('../views/CourseView.vue') },
                { path: 'order', name: 'order', component: () => import('../views/OrderView.vue') },
                {
                    path: 'dispatchPool',
                    name: 'dispatchPool',
                    component: () => import('../views/DispatchPoolView.vue')
                }
            ]
        }
    ]
});

router.beforeEach((to) => {
    const auth = useAuthStore();
    if (to.path !== '/login' && !auth.isLoggedIn) {
        return '/login';
    }
    if (to.path === '/login' && auth.isLoggedIn) {
        return '/';
    }
});

export default router;
