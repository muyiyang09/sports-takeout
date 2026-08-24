<template>
    <view class="page">
        <!-- 状态 -->
        <view class="status-bar" :class="'bar' + order.status">
            <text class="status-text">{{ statusText(order.status) }}</text>
        </view>

        <!-- 地址 -->
        <view class="card">
            <view class="card-title">上门地址</view>
            <view class="addr-name">{{ order.consignee }} {{ order.phone }}</view>
            <view class="addr-detail">{{ order.address }}</view>
        </view>

        <!-- 服务信息 -->
        <view class="card">
            <view class="card-title">服务信息</view>
            <view class="row"><text class="label">服务</text><text>{{ order.orderDishes || '上门私教服务' }}</text></view>
            <view class="row"><text class="label">时段</text><text>{{ order.scheduleDate }} {{ order.timeSlot }}</text></view>
            <view class="row" v-if="order.coachId"><text class="label">教练</text><text>教练ID {{ order.coachId }}</text></view>
            <view class="row"><text class="label">金额</text><text class="price">¥{{ order.amount }}</text></view>
        </view>

        <!-- 订单信息 -->
        <view class="card">
            <view class="card-title">订单信息</view>
            <view class="row"><text class="label">订单号</text><text>{{ order.orderNumber }}</text></view>
            <view class="row"><text class="label">下单时间</text><text>{{ order.submitTime }}</text></view>
            <view class="row" v-if="order.remark"><text class="label">备注</text><text>{{ order.remark }}</text></view>
        </view>

        <!-- 底部操作 -->
        <view class="footer">
            <button v-if="order.status === 1" class="act" @tap="pay">去支付</button>
            <button v-if="order.status === 1 || order.status === 2" class="act ghost" @tap="cancel">取消订单</button>
            <button v-if="order.status === 2 || order.status === 3" class="act ghost" @tap="refund">申请退款</button>
            <button v-if="order.status === 5" class="act" @tap="goReview">评价</button>
        </view>
    </view>
</template>

<script>
const api = require('../../api/index.js');

export default {
    data() {
        return {
            orderId: null,
            order: {}
        };
    },
    onLoad(options) {
        this.orderId = options.id;
        this.loadDetail();
    },
    methods: {
        statusText(s) {
            const map = { 1: '待付款', 2: '待接单', 3: '待服务', 4: '服务中', 5: '已完成', 6: '已取消', 7: '拒单', 8: '退款中', 9: '已退款' };
            return map[s] || '未知';
        },
        async loadDetail() {
            try {
                this.order = await api.getOrderDetail(this.orderId) || {};
            } catch (e) {}
        },
        async pay() {
            try {
                await api.payOrder({ orderNumber: this.order.orderNumber, payMethod: 1 });
                uni.showToast({ title: '支付成功', icon: 'success' });
                this.loadDetail();
            } catch (e) {}
        },
        async cancel() {
            uni.showModal({
                title: '提示',
                content: '确认取消该订单吗？',
                success: async (res) => {
                    if (res.confirm) {
                        try {
                            await api.cancelOrder(this.orderId);
                            uni.showToast({ title: '已取消', icon: 'none' });
                            this.loadDetail();
                        } catch (e) {}
                    }
                }
            });
        },
        async refund() {
            uni.showModal({
                title: '申请退款',
                content: '确认申请退款吗？退款将原路退回。',
                success: async (res) => {
                    if (res.confirm) {
                        try {
                            await api.applyRefund(this.orderId);
                            uni.showToast({ title: '已提交退款申请', icon: 'success' });
                            this.loadDetail();
                        } catch (e) {}
                    }
                }
            });
        },
        goReview() {
            uni.setStorageSync('reviewOrder', this.order);
            uni.navigateTo({ url: '/pages/review/review?orderId=' + this.orderId });
        }
    }
};
</script>

<style>
.page {
    padding: 20rpx;
    padding-bottom: 160rpx;
}
.status-bar {
    background: #00B578;
    color: #fff;
    padding: 40rpx;
    border-radius: 24rpx;
    margin-bottom: 20rpx;
}
.status-bar.bar1, .status-bar.bar6, .status-bar.bar7, .status-bar.bar8 {
    background: #FF8A3D;
}
.status-bar.bar9 {
    background: #9CA3AF;
}
.status-text {
    font-size: 36rpx;
    font-weight: 600;
}
.card {
    background: #fff;
    border-radius: 24rpx;
    padding: 28rpx;
    margin-bottom: 20rpx;
    box-shadow: 0 2rpx 16rpx rgba(17, 24, 39, 0.05);
}
.card-title {
    font-size: 28rpx;
    font-weight: 600;
    margin-bottom: 20rpx;
}
.addr-name {
    font-size: 30rpx;
    font-weight: 600;
}
.addr-detail {
    font-size: 24rpx;
    color: #6B7280;
    margin-top: 8rpx;
}
.row {
    display: flex;
    margin-bottom: 16rpx;
    font-size: 26rpx;
}
.label {
    color: #9CA3AF;
    width: 140rpx;
    flex-shrink: 0;
}
.footer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #fff;
    padding: 20rpx 32rpx;
    display: flex;
    justify-content: flex-end;
    box-shadow: 0 -2rpx 12rpx rgba(17, 24, 39, 0.06);
}
.act {
    background: #00B578;
    color: #fff;
    font-size: 26rpx;
    padding: 0 40rpx;
    border-radius: 999rpx;
    line-height: 68rpx;
    margin-left: 16rpx;
    font-weight: 600;
}
.act.ghost {
    background: #fff;
    color: #6B7280;
    border: 1rpx solid #D1D5DB;
}
</style>
