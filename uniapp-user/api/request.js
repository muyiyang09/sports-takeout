// 请求封装：统一 baseUrl、JWT 鉴权、错误处理
// 用户端 token 头名为 authentication（对应后端 application.yml 的 user-token-name）

const BASE_URL = 'http://localhost:8080';

// 用户端 token 在 localStorage 中的 key
const TOKEN_KEY = 'user_token';

// 过滤 null/undefined/空字符串，避免拼进查询串（如 status=null）
function cleanData(data) {
    if (!data) return {};
    const result = {};
    Object.keys(data).forEach((k) => {
        if (data[k] !== null && data[k] !== undefined && data[k] !== '') {
            result[k] = data[k];
        }
    });
    return result;
}

function request(options) {
    return new Promise((resolve, reject) => {
        const token = uni.getStorageSync(TOKEN_KEY) || '';
        uni.request({
            url: BASE_URL + options.url,
            method: options.method || 'GET',
            data: cleanData(options.data),
            header: Object.assign({
                'Content-Type': 'application/json',
                'authentication': token
            }, options.header || {}),
            success: (res) => {
                // 401：未登录，跳转登录
                if (res.statusCode === 401) {
                    uni.removeStorageSync(TOKEN_KEY);
                    uni.showToast({ title: '请先登录', icon: 'none' });
                    uni.navigateTo({ url: '/pages/my/my' });
                    reject(res);
                    return;
                }
                // 后端统一返回 { code, msg, data }，code=1 成功
                if (res.data && res.data.code === 1) {
                    resolve(res.data.data);
                } else {
                    const msg = (res.data && res.data.msg) || '请求失败';
                    uni.showToast({ title: msg, icon: 'none' });
                    reject(res.data);
                }
            },
            fail: (err) => {
                uni.showToast({ title: '网络异常，请检查后端服务', icon: 'none' });
                reject(err);
            }
        });
    });
}

module.exports = {
    BASE_URL,
    TOKEN_KEY,
    get: (url, data) => request({ url, method: 'GET', data }),
    post: (url, data) => request({ url, method: 'POST', data }),
    put: (url, data) => request({ url, method: 'PUT', data }),
    del: (url, data) => request({ url, method: 'DELETE', data })
};
