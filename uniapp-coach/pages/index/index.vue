<template>
    <view class="page">
        <!-- 教练信息卡 -->
        <view class="profile-card">
            <view class="avatar">{{ avatarText }}</view>
            <view class="profile-info">
                <view class="name">{{ profile.name || '未登录' }}</view>
                <view class="meta">
                    <text class="star">★ {{ profile.rating }}</text>
                    <text v-if="profile.level === 4">金牌教练</text>
                    <text v-else-if="profile.level === 3">高级教练</text>
                    <text v-else-if="profile.level === 2">中级教练</text>
                    <text v-else>初级教练</text>
                </view>
                <view class="bio text-overflow">{{ profile.bio }}</view>
            </view>
        </view>

        <!-- 快捷入口 -->
        <view class="grid card">
            <view class="grid-item" @tap="go('/pages/order/order')">
                <view class="grid-icon">📋</view>
                <view class="grid-text">我的订单</view>
            </view>
            <view class="grid-item" @tap="go('/pages/pool/pool')">
                <view class="grid-icon">🎯</view>
                <view class="grid-text">派单池抢单</view>
            </view>
            <view class="grid-item" @tap="go('/pages/schedule/schedule')">
                <view class="grid-icon">🗓️</view>
                <view class="grid-text">我的排期</view>
            </view>
            <view class="grid-item" @tap="go('/pages/my/my')">
                <view class="grid-icon">👤</view>
                <view class="grid-text">我的</view>
            </view>
        </view>

        <!-- 待办提示 -->
        <view class="todo-card card">
            <view class="todo-title">待办提醒</view>
            <view class="todo-item" @tap="go('/pages/order/order')">
                <view class="todo-left">
                    <view class="todo-main">待接单订单</view>
                    <view class="todo-sub">及时接单，提升响应率</view>
                </view>
                <text class="arrow">›</text>
            </view>
            <view class="todo-item" @tap="go('/pages/pool/pool')">
                <view class="todo-left">
                    <view class="todo-main">派单池可抢单</view>
                    <view class="todo-sub">主动抢单，多接一单</view>
                </view>
                <text class="arrow">›</text>
            </view>
        </view>
    </view>
</template>

<script>
const api = require('../../api/index.js');
const { TOKEN_KEY } = require('../../api/request.js');

export default {
    data() {
        return {
            profile: {},
            avatarText: '教'
        };
    },
    onShow() {
        const token = uni.getStorageSync(TOKEN_KEY);
        if (!token) {
            uni.navigateTo({ url: '/pages/login/login' });
            return;
        }
        this.loadProfile();
    },
    methods: {
        async loadProfile() {
            try {
                this.profile = await api.getProfile() || {};
                this.avatarText = (this.profile.name || '教').charAt(0);
            } catch (e) {}
        },
        go(url) {
            uni.switchTab({ url });
        }
    }
};
</script>

<style>
.page {
    padding: 20rpx;
}
.profile-card {
    background: linear-gradient(150deg, #2F80ED 0%, #56A8F5 100%);
    border-radius: 24rpx;
    padding: 40rpx 32rpx;
    display: flex;
    margin-bottom: 20rpx;
    box-shadow: 0 6rpx 24rpx rgba(47, 128, 237, 0.22);
}
.avatar {
    width: 120rpx;
    height: 120rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.24);
    border: 2rpx solid rgba(255, 255, 255, 0.4);
    color: #fff;
    font-size: 48rpx;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 24rpx;
}
.profile-info {
    flex: 1;
    min-width: 0;
}
.name {
    font-size: 36rpx;
    color: #fff;
    font-weight: 700;
}
.meta {
    margin: 12rpx 0;
    font-size: 24rpx;
    color: rgba(255, 255, 255, 0.92);
}
.star {
    margin-right: 16rpx;
}
.bio {
    font-size: 22rpx;
    color: rgba(255, 255, 255, 0.82);
}
.grid {
    display: flex;
    padding: 32rpx 0;
    margin-bottom: 20rpx;
}
.grid-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
}
.grid-icon {
    font-size: 48rpx;
}
.grid-text {
    font-size: 24rpx;
    color: var(--text-2);
    margin-top: 12rpx;
}
.todo-card {
    padding: 28rpx;
}
.todo-title {
    font-size: 28rpx;
    font-weight: 600;
    margin-bottom: 8rpx;
}
.todo-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 24rpx 0;
}
.todo-item + .todo-item {
    border-top: 1rpx solid var(--line);
}
.todo-main {
    font-size: 28rpx;
    font-weight: 500;
    color: var(--text-1);
}
.todo-sub {
    font-size: 22rpx;
    color: var(--text-3);
    margin-top: 6rpx;
}
.arrow {
    color: #C0C4CC;
    font-size: 40rpx;
}
</style>
