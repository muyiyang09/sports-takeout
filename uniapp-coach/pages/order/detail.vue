<template>
    <view class="page">
        <view class="status-bar" :class="'bar' + order.status">
            <text class="status-text">{{ statusText(order.status) }}</text>
        </view>

        <view class="card">
            <view class="card-title">上门信息</view>
            <view class="addr-name">{{ order.consignee }} {{ order.phone }}</view>
            <view class="addr-detail">{{ order.address }}</view>
            <view class="row"><text class="label">时段</text><text>{{ order.scheduleDate }} {{ order.timeSlot }}</text></view>
        </view>

        <view class="card">
            <view class="card-title">服务信息</view>
            <view class="row"><text class="label">服务</text><text>{{ order.orderDishes || '上门私教服务' }}</text></view>
            <view class="row"><text class="label">金额</text><text class="price">¥{{ order.amount }}</text></view>
            <view class="row" v-if="order.remark"><text class="label">备注</text><text>{{ order.remark }}</text></view>
        </view>

        <view class="card" v-if="order.trainRecord || order.bodyData">
            <view class="card-title">服务记录</view>
            <view class="row" v-if="order.trainRecord"><text class="label">训练</text><text>{{ order.trainRecord }}</text></view>
            <view class="row" v-if="order.bodyData"><text class="label">体测</text><text>{{ order.bodyData }}</text></view>
        </view>

        <view class="footer">
            <button v-if="order.status === 2" class="act ghost" @tap="reject">拒单</button>
            <button v-if="order.status === 2" class="act" @tap="confirm">接单</button>
            <button v-if="order.status === 3" class="act" @tap="start">开始服务</button>
            <button v-if="order.status === 4" class="act" @tap="openComplete">完成服务</button>
        </view>

        <!-- 完成服务弹窗 -->
        <view v-if="showComplete" class="mask" @tap="showComplete = false">
            <view class="popup" @tap.stop>
                <view class="popup-title">完成服务</view>
                <textarea class="popup-input" v-model="trainRecord" placeholder="训练记录（如：深蹲3组、平板支撑3组）" />
                <textarea class="popup-input" v-model="bodyData" placeholder="体测数据（如：体重80kg、体脂25%）" />
                <view class="popup-actions">
                    <button class="popup-btn ghost" @tap="showComplete = false">取消</button>
                    <button class="popup-btn" @tap="complete">提交</button>
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
            orderId: null,
            order: {},
            coachId: null,
            showComplete: false,
            trainRecord: '',
            bodyData: ''
        };
    },
    onLoad(options) {
        this.orderId = options.id;
        this.coachId = uni.getStorageSync(COACH_ID_KEY);
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
        async confirm() {
            try {
                await api.confirmOrder(this.orderId, this.coachId);
                uni.showToast({ title: '已接单', icon: 'success' });
                this.loadDetail();
            } catch (e) {}
        },
        async reject() {
            uni.showModal({
                title: '拒单原因',
                editable: true,
                placeholderText: '请输入拒单原因',
                success: async (res) => {
                    if (res.confirm) {
                        try {
                            await api.rejectOrder(this.orderId, this.coachId, res.content);
                            uni.showToast({ title: '已拒单', icon: 'none' });
                            this.loadDetail();
                        } catch (e) {}
                    }
                }
            });
        },
        async start() {
            try {
                await api.startService(this.orderId, this.coachId);
                uni.showToast({ title: '已开始服务', icon: 'success' });
                this.loadDetail();
            } catch (e) {}
        },
        openComplete() {
            this.showComplete = true;
        },
        async complete() {
            try {
                await api.completeService({
                    id: this.orderId,
                    coachId: this.coachId,
                    trainRecord: this.trainRecord,
                    bodyData: this.bodyData
                });
                uni.showToast({ title: '服务已完成', icon: 'success' });
                this.showComplete = false;
                this.loadDetail();
            } catch (e) {}
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
    background: #2F80ED;
    color: #fff;
    padding: 40rpx;
    border-radius: 24rpx;
    margin-bottom: 20rpx;
}
.status-bar.bar5 {
    background: #00B578;
}
.status-bar.bar6, .status-bar.bar7 {
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
    margin: 10rpx 0 20rpx;
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
    background: #2F80ED;
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
.mask {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 999;
}
.popup {
    width: 80%;
    background: #fff;
    border-radius: 24rpx;
    padding: 40rpx;
}
.popup-title {
    font-size: 30rpx;
    font-weight: 600;
    margin-bottom: 24rpx;
}
.popup-input {
    width: 100%;
    height: 140rpx;
    background: #F6F7F9;
    border-radius: 12rpx;
    padding: 16rpx;
    font-size: 26rpx;
    margin-bottom: 20rpx;
    box-sizing: border-box;
}
.popup-actions {
    display: flex;
    justify-content: flex-end;
}
.popup-btn {
    background: #2F80ED;
    color: #fff;
    font-size: 26rpx;
    padding: 0 40rpx;
    border-radius: 999rpx;
    line-height: 64rpx;
    margin-left: 16rpx;
}
.popup-btn.ghost {
    background: #F6F7F9;
    color: #6B7280;
}
</style>
