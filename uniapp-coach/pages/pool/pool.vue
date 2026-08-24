<template>
    <view class="page">
        <view v-if="poolList.length === 0" class="empty">
            <text class="empty-icon">🎯</text>
            <text class="empty-text">派单池暂无可抢订单</text>
            <text class="empty-sub">有新的派单订单会显示在这里</text>
        </view>

        <view v-for="item in poolList" :key="item.id" class="pool-card card">
            <view class="pool-head">
                <text class="pool-time">{{ item.scheduleDate }} {{ item.timeSlot }}</text>
                <text class="pool-amount">¥{{ item.amount }}</text>
            </view>
            <view class="pool-addr">{{ item.address }}</view>
            <view class="pool-contact">联系人：{{ item.consignee }} {{ item.phone }}</view>
            <view class="pool-foot">
                <text class="pool-expire" v-if="item.expireTime">超时：{{ item.expireTime }}</text>
                <button class="seize-btn" @tap="seize(item)">抢单</button>
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
            poolList: [],
            coachId: null
        };
    },
    onLoad() {
        this.coachId = uni.getStorageSync(COACH_ID_KEY);
    },
    onShow() {
        this.loadPool();
    },
    methods: {
        async loadPool() {
            try {
                this.poolList = await api.getDispatchPool('') || [];
            } catch (e) {}
        },
        async seize(item) {
            uni.showModal({
                title: '抢单确认',
                content: '确认抢这个订单吗？',
                success: async (res) => {
                    if (res.confirm) {
                        try {
                            await api.seizeOrder(item.id, this.coachId);
                            uni.showToast({ title: '抢单成功', icon: 'success' });
                            this.loadPool();
                        } catch (e) {}
                    }
                }
            });
        }
    }
};
</script>

<style>
.page {
    padding: 20rpx;
}
.pool-card {
    margin-bottom: 20rpx;
    border-left: 6rpx solid #2F80ED;
}
.pool-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12rpx;
}
.pool-time {
    font-size: 30rpx;
    font-weight: 600;
}
.pool-amount {
    color: #FF6B35;
    font-size: 30rpx;
    font-weight: 600;
}
.pool-addr {
    font-size: 26rpx;
    color: #6B7280;
    margin-bottom: 10rpx;
}
.pool-contact {
    font-size: 24rpx;
    color: #9CA3AF;
    margin-bottom: 16rpx;
}
.pool-foot {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.pool-expire {
    font-size: 22rpx;
    color: #FF6B35;
}
.seize-btn {
    background: #2F80ED;
    color: #fff;
    font-size: 26rpx;
    padding: 0 40rpx;
    border-radius: 999rpx;
    line-height: 64rpx;
    font-weight: 600;
}
</style>
