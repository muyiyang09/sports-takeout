// 教练端请求封装：统一 baseUrl、JWT 鉴权、错误处理
// 教练端 token 头名为 token（对应后端 coach-token-name）

const BASE_URL = 'http://localhost:8080';
const TOKEN_KEY = 'coach_token';
const COACH_ID_KEY = 'coach_id';

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
                'token': token
            }, options.header || {}),
            success: (res) => {
                if (res.statusCode === 401) {
                    uni.removeStorageSync(TOKEN_KEY);
                    uni.showToast({ title: '请先登录', icon: 'none' });
                    uni.navigateTo({ url: '/pages/login/login' });
                    reject(res);
                    return;
                }
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

// 文件上传（头像/证书图片）
function uploadFile(filePath) {
    return new Promise((resolve, reject) => {
        const token = uni.getStorageSync(TOKEN_KEY) || '';
        uni.uploadFile({
            url: BASE_URL + '/coach/common/upload',
            filePath: filePath,
            name: 'file',
            header: { 'token': token },
            success: (res) => {
                try {
                    const data = JSON.parse(res.data);
                    if (data.code === 1) {
                        resolve(data.data);
                    } else {
                        uni.showToast({ title: data.msg || '上传失败', icon: 'none' });
                        reject(data);
                    }
                } catch (e) {
                    reject(e);
                }
            },
            fail: reject
        });
    });
}

// 把后端返回的相对路径转成完整可访问 URL
function fullUrl(path) {
    if (!path) return '';
    if (path.indexOf('http') === 0) return path;
    return BASE_URL + path;
}

module.exports = {
    BASE_URL,
    TOKEN_KEY,
    COACH_ID_KEY,
    fullUrl,
    uploadFile,
    get: (url, data) => request({ url, method: 'GET', data }),
    post: (url, data) => request({ url, method: 'POST', data }),
    put: (url, data) => request({ url, method: 'PUT', data })
};
