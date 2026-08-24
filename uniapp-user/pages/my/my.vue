<template>
    <view class="page">
        <!-- 用户信息 / 登录 -->
        <view class="user-card">
            <view v-if="userInfo" class="user-info">
                <view class="avatar">{{ avatarText }}</view>
                <view class="user-name">{{ userInfo.name || '微信用户' }}</view>
            </view>
            <view v-else class="user-info" @tap="login">
                <view class="avatar">未</view>
                <view class="user-name">点击登录</view>
            </view>
        </view>

        <!-- 功能入口 -->
        <view class="menu">
            <view class="menu-item" @tap="go('/pages/order/order')">
                <text>我的订单</text>
                <text class="arrow">›</text>
            </view>
            <view class="menu-item" @tap="go('/pages/address/address')">
                <text>上门地址</text>
                <text class="arrow">›</text>
            </view>
            <view class="menu-item" @tap="go('/pages/agreement/agreement')">
                <text>协议与政策</text>
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
            userInfo: null,
            avatarText: '客'
        };
    },
    onShow() {
        this.checkLogin();
    },
    methods: {
        checkLogin() {
            const token = uni.getStorageSync(TOKEN_KEY);
            if (token) {
                this.userInfo = uni.getStorageSync('user_info');
                this.avatarText = (this.userInfo.name || '客').charAt(0);
            }
        },
        async login() {
            // 微信登录：获取 code -> 后端 code2session 换 openid
            // 注意：需在 manifest.json 的 mp-weixin.appid 配置真实 appid，且后端 application-dev.yml 配置对应 appid/secret
            uni.login({
                provider: 'weixin',
                success: async (res) => {
                    try {
                        const data = await api.login(res.code);
                        uni.setStorageSync(TOKEN_KEY, data.token);
                        uni.setStorageSync('user_info', { id: data.id, openid: data.openid });
                        this.userInfo = { id: data.id, name: '' };
                        this.avatarText = '客';
                        uni.showToast({ title: '登录成功', icon: 'success' });
                    } catch (e) {
                        // 无 appid/secret 时会失败，提示配置
                        uni.showToast({ title: '登录失败，请检查 appid/secret 配置', icon: 'none' });
                    }
                },
                fail: () => {
                    uni.showToast({ title: '微信登录失败', icon: 'none' });
                }
            });
        },
        go(url) {
            uni.navigateTo({ url });
        }
    }
};
</script>

<style>
.page {
    padding: 20rpx;
}
.user-card {
    background: linear-gradient(135deg, #00B578, #00D68F);
    border-radius: 16rpx;
    padding: 48rpx 32rpx;
    margin-bottom: 20rpx;
}
.user-info {
    display: flex;
    align-items: center;
}
.avatar {
    width: 100rpx;
    height: 100rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.3);
    color: #fff;
    font-size: 40rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 24rpx;
}
.user-name {
    font-size: 34rpx;
    color: #fff;
    font-weight: bold;
}
.menu {
    background: #fff;
    border-radius: 16rpx;
    overflow: hidden;
}
.menu-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 32rpx 28rpx;
    border-bottom: 1rpx solid #f2f3f5;
    font-size: 28rpx;
}
.arrow {
    color: #ccc;
    font-size: 36rpx;
}
</style>
