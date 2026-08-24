// 管理端请求封装：统一 token 鉴权、错误处理
// 管理端 token 头名为 token（对应后端 admin-token-name）

const TOKEN_KEY = 'admin_token';

export function getToken() {
    return localStorage.getItem(TOKEN_KEY) || '';
}

export function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
}

async function request(url, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        token,
        ...(options.headers || {})
    };

    let body;
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
function qs(params) {
    if (!params) return '';
    const keys = Object.keys(params).filter((k) => params[k] !== undefined && params[k] !== null && params[k] !== '');
    if (keys.length === 0) return '';
    return '?' + keys.map((k) => `${encodeURIComponent(k)}=${encodeURIComponent(params[k])}`).join('&');
}

export default {
    get: (url, params) => request(url + qs(params), { method: 'GET' }),
    post: (url, data) => request(url, { method: 'POST', data }),
    put: (url, data) => request(url, { method: 'PUT', data }),
    del: (url) => request(url, { method: 'DELETE' })
};
