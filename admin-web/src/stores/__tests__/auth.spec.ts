import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useAuthStore } from '../auth';
import { getToken, clearToken } from '../../api';

describe('auth store', () => {
    beforeEach(() => {
        setActivePinia(createPinia());
        clearToken();
    });

    it('初始未登录', () => {
        const auth = useAuthStore();
        expect(auth.isLoggedIn).toBe(false);
    });

    it('login 后 isLoggedIn 为 true 且写入 localStorage', () => {
        const auth = useAuthStore();
        auth.login('abc');
        expect(auth.isLoggedIn).toBe(true);
        expect(getToken()).toBe('abc');
    });

    it('logout 清除 token', () => {
        const auth = useAuthStore();
        auth.login('abc');
        auth.logout();
        expect(auth.isLoggedIn).toBe(false);
        expect(getToken()).toBe('');
    });
});
