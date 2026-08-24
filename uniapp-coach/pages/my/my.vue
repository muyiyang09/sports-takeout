<template>
    <view class="page">
        <!-- 教练信息 -->
        <view class="profile-card">
            <view class="avatar-box" @tap="editAvatar">
                <image v-if="avatarUrl" class="avatar-img" :src="avatarUrl" mode="aspectFill" />
                <view v-else class="avatar-text">{{ firstChar(profile.name) }}</view>
                <view class="avatar-edit">改</view>
            </view>
            <view class="profile-info">
                <view class="name">{{ profile.name }}</view>
                <view class="meta">
                    <text class="star">★ {{ profile.rating }}</text>
                    <text>{{ profile.cityName }}</text>
                </view>
            </view>
        </view>

        <!-- 我的评价 -->
        <view class="card">
            <view class="card-title">我的评价</view>
            <view v-if="reviews.length === 0" class="empty">
                <text class="empty-icon">📝</text>
                <text class="empty-text">暂无评价</text>
            </view>
            <view v-for="item in reviews" :key="item.id" class="review-item">
                <view class="review-head">
                    <text class="review-star">教练 {{ item.coachRating }}★ · 课程 {{ item.courseRating }}★</text>
                </view>
                <view class="review-content">{{ item.content }}</view>
            </view>
        </view>

        <!-- 退出 -->
        <button class="logout-btn" @tap="logout">退出登录</button>
    </view>
</template>

<script>
const api = require('../../api/index.js');
const { TOKEN_KEY, COACH_ID_KEY, fullUrl } = require('../../api/request.js');

export default {
    data() {
        return {
            profile: {},
            reviews: []
        };
    },
    computed: {
        avatarUrl() {
            return fullUrl(this.profile.avatar);
        }
    },
    onShow() {
        this.loadProfile();
        this.loadReviews();
    },
    methods: {
        firstChar(name) {
            return (name || '教').charAt(0);
        },
        async loadProfile() {
            try {
                this.profile = await api.getProfile() || {};
            } catch (e) {}
        },
        async loadReviews() {
            try {
                const res = await api.getReviews({ page: 1, pageSize: 20 });
                this.reviews = (res && res.records) || [];
            } catch (e) {}
        },
        editAvatar() {
            uni.chooseImage({
                count: 1,
                sizeType: ['compressed'],
                success: async (res) => {
                    const path = res.tempFilePaths[0];
                    try {
                        const url = await api.uploadAvatar(path);
                        await api.updateProfile({ avatar: url });
                        uni.showToast({ title: '头像已更新', icon: 'success' });
                        this.loadProfile();
                    } catch (e) {}
                }
            });
        },
        logout() {
            uni.showModal({
                title: '提示',
                content: '确认退出登录吗？',
                success: (res) => {
                    if (res.confirm) {
                        uni.removeStorageSync(TOKEN_KEY);
                        uni.removeStorageSync(COACH_ID_KEY);
                        uni.removeStorageSync('coach_info');
                        uni.reLaunch({ url: '/pages/index/index' });
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
.profile-card {
    background: linear-gradient(135deg, #2F80ED, #56CCF2);
    border-radius: 16rpx;
    padding: 40rpx 32rpx;
    display: flex;
    align-items: center;
    margin-bottom: 20rpx;
}
.avatar-box {
    position: relative;
    width: 110rpx;
    height: 110rpx;
    margin-right: 24rpx;
}
.avatar-img {
    width: 110rpx;
    height: 110rpx;
    border-radius: 50%;
}
.avatar-text {
    width: 110rpx;
    height: 110rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.24);
    border: 2rpx solid rgba(255, 255, 255, 0.4);
    color: #fff;
    font-size: 44rpx;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
}
.avatar-edit {
    position: absolute;
    right: -6rpx;
    bottom: -6rpx;
    width: 40rpx;
    height: 40rpx;
    border-radius: 50%;
    background: #fff;
    color: #2F80ED;
    font-size: 20rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.15);
}
.profile-info {
    flex: 1;
}
.name {
    font-size: 36rpx;
    color: #fff;
    font-weight: bold;
}
.meta {
    margin-top: 10rpx;
    font-size: 24rpx;
    color: rgba(255, 255, 255, 0.9);
}
.star {
    margin-right: 16rpx;
}
.card {
    background: #fff;
    border-radius: 16rpx;
    padding: 28rpx;
    margin-bottom: 20rpx;
}
.card-title {
    font-size: 28rpx;
    font-weight: bold;
    margin-bottom: 20rpx;
}
.review-item {
    padding: 20rpx 0;
    border-bottom: 1rpx solid #f2f3f5;
}
.review-head {
    margin-bottom: 10rpx;
}
.review-star {
    font-size: 24rpx;
    color: #ff9500;
}
.review-content {
    font-size: 26rpx;
    color: #666;
}
.empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 40rpx 0;
    color: #9CA3AF;
}
.empty-icon {
    font-size: 64rpx;
    margin-bottom: 16rpx;
}
.empty-text {
    font-size: 24rpx;
}
.logout-btn {
    background: #fff;
    color: #ff6b35;
    font-size: 30rpx;
    border-radius: 44rpx;
    line-height: 84rpx;
}
</style>
