<template>
    <view class="page">
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

        <view v-if="orders.length === 0" class="empty">
            <text class="empty-icon">📋</text>
            <text class="empty-text">暂无订单</text>
            <text class="empty-sub">有订单时会显示在这里</text>
        </view>

        <view v-for="item in orders" :key="item.id" class="order-card card" @tap="goDetail(item)">
            <view class="order-head">
                <text class="order-no">{{ item.orderNumber }}</text>
                <text class="order-status" :class="'st' + item.status">{{ statusText(item.status) }}</text>
            </view>
            <view class="order-body">
                <view class="order-course">{{ item.orderDishes || '上门私教服务' }}</view>
                <view class="order-meta">上门：{{ item.scheduleDate }} {{ item.timeSlot }}</view>
                <view class="order-meta">地址：{{ item.address }}</view>
                <view class="order-meta">联系人：{{ item.consignee }} {{ item.phone }}</view>
            </view>
            <view class="order-foot">
                <text class="order-amount">¥{{ item.amount }}</text>
                <view class="order-actions">
                    <text v-if="item.status === 2" class="act-btn" @tap.stop="confirm(item)">接单</text>
                    <text v-if="item.status === 3" class="act-btn" @tap.stop="start(item)">开始服务</text>
                </view>
            </view>
        </view>
    </view>
</template>

<script>
const api = require('../../api/index.js');
const { COACH_ID_KEY } = require('../../api/request.js');

export default {
    data() {
        return {
            tabs: [
                { label: '全部', value: null },
                { label: '待接单', value: 2 },
                { label: '待服务', value: 3 },
                { label: '服务中', value: 4 },
                { label: '已完成', value: 5 }
            ],
            activeStatus: null,
            orders: [],
            page: 1,
            pageSize: 10,
            coachId: null
        };
    },
    onLoad() {
        this.coachId = uni.getStorageSync(COACH_ID_KEY);
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
                const res = await api.getOrderList({ page: this.page, pageSize: this.pageSize, status: this.activeStatus, coachId: this.coachId });
                this.orders = (res && res.records) || [];
            } catch (e) {}
        },
        goDetail(item) {
            uni.navigateTo({ url: '/pages/order/detail?id=' + item.id });
        },
        async confirm(item) {
            try {
                await api.confirmOrder(item.id, this.coachId);
                uni.showToast({ title: '已接单', icon: 'success' });
                this.loadOrders();
            } catch (e) {}
        },
        async start(item) {
            try {
                await api.startService(item.id, this.coachId);
                uni.showToast({ title: '已开始服务', icon: 'success' });
                this.loadOrders();
            } catch (e) {}
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
    color: #2F80ED;
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
    color: #2F80ED;
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
    color: #FF6B35;
    font-size: 28rpx;
    font-weight: 600;
}
.act-btn {
    background: #2F80ED;
    color: #fff;
    font-size: 24rpx;
    padding: 8rpx 32rpx;
    border-radius: 999rpx;
    font-weight: 600;
}
</style>
