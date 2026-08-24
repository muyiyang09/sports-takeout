// 教练端所有接口方法
const request = require('./request.js');

module.exports = {
    // ---- 登录 / 注册 / 资料 ----
    login(phone, password) {
        return request.post('/coach/coach/login', { phone, password });
    },
    register(data) {
        return request.post('/coach/coach/register', data);
    },
    getProfile() {
        return request.get('/coach/coach');
    },
    updateProfile(data) {
        return request.put('/coach/coach', data);
    },
    uploadAvatar(filePath) {
        return request.uploadFile(filePath);
    },

    // ---- 排期 ----
    generateSchedule(data) {
        return request.post('/coach/schedule/generate', data);
    },
    getSchedule(startDate, endDate) {
        return request.get('/coach/schedule', { startDate, endDate });
    },

    // ---- 订单 ----
    getOrderList(params) {
        return request.get('/coach/order/list', params);
    },
    confirmOrder(id, coachId) {
        return request.put('/coach/order/confirm?id=' + id + '&coachId=' + coachId);
    },
    rejectOrder(id, coachId, reason) {
        return request.put('/coach/order/reject?id=' + id + '&coachId=' + coachId + '&reason=' + encodeURIComponent(reason || ''));
    },
    seizeOrder(poolId, coachId) {
        return request.post('/coach/order/seize?poolId=' + poolId + '&coachId=' + coachId);
    },
    startService(id, coachId) {
        return request.put('/coach/order/startService?id=' + id + '&coachId=' + coachId);
    },
    completeService(data) {
        return request.put('/coach/order/completeService', data);
    },
    getDispatchPool(cityCode) {
        return request.get('/coach/order/dispatchPool', { cityCode });
    },
    getOrderDetail(id) {
        return request.get('/coach/order/details/' + id);
    },

    // ---- 评价 ----
    getReviews(params) {
        return request.get('/coach/review/page', params);
    }
};
