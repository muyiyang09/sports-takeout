<template>
    <view class="page">
        <!-- 状态 tab -->
        <view class="tabs">
            <view
                v-for="(t, i) in tabs"
                :key="i"
                class="tab-item"
                :class="{ active: activeStatus === t.value }"
                @tap="switchTab(t.value)"
            >
                {{ t.label }}
            </view>
        </view>

        <!-- 订单列表 -->
        <view v-if="orders.length === 0" class="empty">
            <text class="empty-icon">📋</text>
            <text class="empty-text">暂无订单</text>
            <text class="empty-sub">去首页预约一位教练吧</text>
        </view>

        <view v-for="item in orders" :key="item.id" class="order-card card" @tap="goDetail(item)">
            <view class="order-head">
                <text class="order-no">{{ item.orderNumber }}</text>
                <text class="order-status" :class="'st' + item.status">{{ statusText(item.status) }}</text>
            </view>
            <view class="order-body">
                <view class="order-course">{{ item.orderDishes || '上门私教服务' }}</view>
                <view class="order-meta">{{ item.scheduleDate }} {{ item.timeSlot }}</view>
            </view>
            <view class="order-foot">
                <text class="order-amount">合计 <text class="price">¥{{ item.amount }}</text></text>
                <view class="order-actions">
                    <text v-if="item.status === 1" class="act-btn" @tap.stop="pay(item)">去支付</text>
                    <text v-if="item.status === 1 || item.status === 2" class="act-btn ghost" @tap.stop="cancel(item)">取消</text>
                    <text v-if="item.status === 2 || item.status === 3" class="act-btn ghost" @tap.stop="refund(item)">退款</text>
                    <text v-if="item.status === 5" class="act-btn" @tap.stop="goReview(item)">评价</text>
                </view>
            </view>
        </view>
    </view>
</template>

<script>
const api = require('../../api/index.js');

export default {
    data() {
        return {
            tabs: [
                { label: '全部', value: null },
                { label: '待付款', value: 1 },
                { label: '待接单', value: 2 },
                { label: '待服务', value: 3 },
                { label: '服务中', value: 4 },
                { label: '已完成', value: 5 },
                { label: '已取消', value: 6 }
            ],
            activeStatus: null,
            orders: [],
            page: 1,
            pageSize: 10
        };
    },
    onLoad() {
        this.loadOrders();
    },
    onShow() {
        this.loadOrders();
    },
    methods: {
        statusText(s) {
            const map = { 1: '待付款', 2: '待接单', 3: '待服务', 4: '服务中', 5: '已完成', 6: '已取消', 7: '拒单', 8: '退款中', 9: '已退款' };
            return map[s] || '未知';
        },
        switchTab(v) {
            this.activeStatus = v;
            this.page = 1;
            this.loadOrders();
        },
        async loadOrders() {
            try {
                const res = await api.getOrderHistory({ page: this.page, pageSize: this.pageSize, status: this.activeStatus });
                this.orders = (res && res.records) || [];
            } catch (e) {}
        },
        goDetail(item) {
            uni.navigateTo({ url: '/pages/order/detail?id=' + item.id });
        },
        async pay(item) {
            try {
                await api.payOrder({ orderNumber: item.orderNumber, payMethod: 1 });
                uni.showToast({ title: '支付成功', icon: 'success' });
                this.loadOrders();
            } catch (e) {}
        },
        async cancel(item) {
            uni.showModal({
                title: '提示',
                content: '确认取消该订单吗？',
                success: async (res) => {
                    if (res.confirm) {
                        try {
                            await api.cancelOrder(item.id);
                            uni.showToast({ title: '已取消', icon: 'none' });
                            this.loadOrders();
                        } catch (e) {}
                    }
                }
            });
        },
        async refund(item) {
            uni.showModal({
                title: '申请退款',
                content: '确认申请退款吗？退款将原路退回。',
                success: async (res) => {
                    if (res.confirm) {
                        try {
                            await api.applyRefund(item.id);
                            uni.showToast({ title: '已提交退款申请', icon: 'success' });
                            this.loadOrders();
                        } catch (e) {}
                    }
                }
            });
        },
        goReview(item) {
            uni.setStorageSync('reviewOrder', item);
            uni.navigateTo({ url: '/pages/review/review?orderId=' + item.id });
        }
    }
};
</script>

<style>
.page {
    padding: 20rpx;
}
.tabs {
    display: flex;
    background: #fff;
    border-radius: 24rpx;
    padding: 16rpx 8rpx;
    margin-bottom: 20rpx;
    box-shadow: 0 2rpx 16rpx rgba(17, 24, 39, 0.04);
}
.tab-item {
    flex: 1;
    text-align: center;
    font-size: 24rpx;
    color: #6B7280;
    padding: 8rpx 0;
}
.tab-item.active {
    color: #00B578;
    font-weight: 600;
}
.order-card {
    margin-bottom: 20rpx;
}
.order-head {
    display: flex;
    justify-content: space-between;
    border-bottom: 1rpx solid #EEF0F3;
    padding-bottom: 16rpx;
}
.order-no {
    font-size: 24rpx;
    color: #9CA3AF;
}
.order-status {
    font-size: 24rpx;
    font-weight: 600;
    color: #00B578;
}
.order-status.st1, .order-status.st6, .order-status.st7 {
    color: #FF6B35;
}
.order-body {
    padding: 20rpx 0;
}
.order-course {
    font-size: 30rpx;
    font-weight: 600;
}
.order-meta {
    font-size: 24rpx;
    color: #6B7280;
    margin-top: 10rpx;
}
.order-foot {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1rpx solid #EEF0F3;
    padding-top: 16rpx;
}
.order-amount {
    font-size: 26rpx;
}
.act-btn {
    border: 1rpx solid #00B578;
    color: #00B578;
    font-size: 24rpx;
    padding: 8rpx 28rpx;
    border-radius: 999rpx;
    margin-left: 16rpx;
}
.act-btn.ghost {
    border-color: #D1D5DB;
    color: #6B7280;
}
</style>
