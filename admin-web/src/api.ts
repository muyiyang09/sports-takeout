// 管理端请求封装：统一 token 鉴权、错误处理
// 管理端 token 头名为 token（对应后端 admin-token-name）

const TOKEN_KEY = 'admin_token';

export function getToken(): string {
    return localStorage.getItem(TOKEN_KEY) || '';
}

export function setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
    localStorage.removeItem(TOKEN_KEY);
}

interface RequestOptions {
    method?: string;
    data?: unknown;
    headers?: Record<string, string>;
}

async function request(url: string, options: RequestOptions = {}) {
    const token = getToken();
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        token,
        ...(options.headers || {})
    };

    let body: string | undefined;
    if (options.data !== undefined) {
        body = JSON.stringify(options.data);
    }

    const res = await fetch(url, {
        method: options.method || 'GET',
        headers,
        body
    });

    if (res.status === 401) {
        clearToken();
        throw new Error('未登录或登录已过期');
    }

    const json = await res.json();
    if (json.code === 1) {
        return json.data;
    }
    throw new Error(json.msg || '请求失败');
}

// 拼接 GET 查询参数
function qs(params?: Record<string, unknown>): string {
    if (!params) return '';
    const keys = Object.keys(params).filter(
        (k) => params[k] !== undefined && params[k] !== null && params[k] !== ''
    );
    if (keys.length === 0) return '';
    return (
        '?' +
        keys.map((k) => `${encodeURIComponent(k)}=${encodeURIComponent(String(params[k]))}`).join('&')
    );
}

export default {
    get: (url: string, params?: Record<string, unknown>) =>
        request(url + qs(params), { method: 'GET' }),
    post: (url: string, data?: unknown) => request(url, { method: 'POST', data }),
    put: (url: string, data?: unknown) => request(url, { method: 'PUT', data }),
    del: (url: string) => request(url, { method: 'DELETE' })
};
