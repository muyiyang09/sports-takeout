import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import { getToken, setToken, clearToken } from '../api';

// 登录态集中到 Pinia（§5.21），替代原先散落在 App.vue 的 ref + localStorage 闭包变量
export const useAuthStore = defineStore('auth', () => {
    const token = ref(getToken());
    const isLoggedIn = computed(() => !!token.value);

    function login(t: string) {
        setToken(t);
        token.value = t;
    }

    function logout() {
        clearToken();
        token.value = '';
    }

    return { token, isLoggedIn, login, logout };
});
