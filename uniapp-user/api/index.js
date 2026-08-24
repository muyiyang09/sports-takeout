// 用户端所有接口方法
const request = require('./request.js');

module.exports = {
    // ---- 登录 ----
    login(code) {
        return request.post('/user/user/login', { code });
    },

    // ---- 分类 / 课程 ----
    getCategoryList(type) {
        return request.get('/user/category/list', { type });
    },
    getCourseList(categoryId) {
        return request.get('/user/course/list', { categoryId });
    },

    // ---- 教练 ----
    getCoachList(params) {
        // params: { cityCode, page, pageSize }
        return request.get('/user/coach/list', params);
    },
    getCoachDetail(id) {
        return request.get('/user/coach/' + id);
    },
    getCoachSchedule(coachId, date) {
        return request.get('/user/coach/' + coachId + '/schedule', { date });
    },

    // ---- 地址 ----
    getAddressList() {
        return request.get('/user/addressBook/list');
    },
    getDefaultAddress() {
        return request.get('/user/addressBook/default');
    },
    saveAddress(data) {
        return request.post('/user/addressBook', data);
    },
    updateAddress(data) {
        return request.put('/user/addressBook', data);
    },
    deleteAddress(id) {
        return request.del('/user/addressBook', { id });
    },
    setDefaultAddress(data) {
        return request.put('/user/addressBook/default', data);
    },

    // ---- 订单 ----
    submitOrder(data) {
        return request.post('/user/order/submit', data);
    },
    payOrder(data) {
        return request.put('/user/order/payment', data);
    },
    getOrderHistory(params) {
        // params: { page, pageSize, status }
        return request.get('/user/order/historyOrders', params);
    },
    getOrderDetail(id) {
        return request.get('/user/order/orderDetail/' + id);
    },
    cancelOrder(id) {
        return request.put('/user/order/cancel/' + id);
    },
    applyRefund(id) {
        return request.put('/user/order/refund/' + id);
    },
    remindOrder(id) {
        return request.get('/user/order/reminder/' + id);
    },

    // ---- 评价 ----
    submitReview(data) {
        return request.post('/user/order/review', data);
    },
    getReview(orderId) {
        return request.get('/user/order/review/' + orderId);
    }
};
