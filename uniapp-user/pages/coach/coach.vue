<template>
    <view class="page">
        <!-- 就近派单入口 -->
        <view class="dispatch-card" @tap="goDispatch">
            <view class="dispatch-left">
                <view class="dispatch-title">附近教练就近派单</view>
                <view class="dispatch-sub">平台按你的位置派单，无需自己选</view>
            </view>
            <view class="dispatch-btn">派单</view>
        </view>

        <!-- 教练列表 -->
        <view v-if="coachList.length === 0" class="empty">
            <text class="empty-icon">🏃</text>
            <text class="empty-text">暂无教练</text>
            <text class="empty-sub">附近教练入驻后会展示在这里</text>
        </view>

        <view v-for="item in coachList" :key="item.id" class="coach-card card" @tap="goDetail(item)">
            <view class="avatar">{{ firstChar(item.name) }}</view>
            <view class="coach-info">
                <view class="coach-name">
                    {{ item.name }}
                    <text class="level-badge" :class="'lv' + item.level">{{ levelText(item.level) }}</text>
                </view>
                <view class="coach-meta">
                    <text class="star">★ {{ item.rating }}</text>
                    <text class="dot">·</text>
                    <text>{{ item.serviceRadiusKm }}km</text>
                    <text class="dot">·</text>
                    <text>{{ item.cityName }}</text>
                </view>
                <view class="coach-bio text-overflow">{{ item.bio }}</view>
            </view>
            <view class="coach-right">
                <text class="price">¥{{ coursePrice }}</text>
                <text class="select-btn">选TA</text>
            </view>
        </view>
    </view>
</template>

<script>
const api = require('../../api/index.js');

export default {
    data() {
        return {
            coachList: [],
            page: 1,
            pageSize: 20,
            course: null
        };
    },
    computed: {
        coursePrice() {
            return this.course ? this.course.price : '--';
        }
    },
    onLoad() {
        this.course = uni.getStorageSync('bookingCourse') || null;
        this.loadCoaches();
    },
    methods: {
        firstChar(name) {
            return (name || '').charAt(0) || '?';
        },
        levelText(level) {
            const map = { 1: '初级', 2: '中级', 3: '高级', 4: '金牌' };
            return map[level] || '初级';
        },
        async loadCoaches() {
            try {
                const res = await api.getCoachList({ cityCode: '', page: this.page, pageSize: this.pageSize });
                this.coachList = (res && res.records) || [];
            } catch (e) {}
        },
        goDetail(coach) {
            uni.setStorageSync('bookingCoach', coach);
            uni.navigateTo({ url: '/pages/coach/detail?id=' + coach.id });
        },
        goDispatch() {
            uni.removeStorageSync('bookingCoach');
            uni.removeStorageSync('bookingSchedule');
            uni.navigateTo({ url: '/pages/booking/booking?mode=dispatch' });
        }
    }
};
</script>

<style>
.page {
    padding: 20rpx;
}
.dispatch-card {
    background: linear-gradient(150deg, #00B578, #00C48A);
    border-radius: 24rpx;
    padding: 32rpx 28rpx;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20rpx;
    box-shadow: 0 6rpx 20rpx rgba(0, 181, 120, 0.2);
}
.dispatch-left {
    display: flex;
    flex-direction: column;
}
.dispatch-title {
    font-size: 30rpx;
    font-weight: 600;
    color: #fff;
}
.dispatch-sub {
    font-size: 22rpx;
    color: rgba(255, 255, 255, 0.85);
    margin-top: 8rpx;
}
.dispatch-btn {
    background: rgba(255, 255, 255, 0.2);
    color: #fff;
    padding: 12rpx 36rpx;
    border-radius: 999rpx;
    font-size: 26rpx;
    font-weight: 600;
}
.coach-card {
    display: flex;
    margin-bottom: 20rpx;
}
.avatar {
    width: 96rpx;
    height: 96rpx;
    border-radius: 50%;
    background: #00B578;
    color: #fff;
    font-size: 40rpx;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 20rpx;
    flex-shrink: 0;
}
.coach-info {
    flex: 1;
    min-width: 0;
}
.coach-name {
    font-size: 30rpx;
    font-weight: 600;
    display: flex;
    align-items: center;
}
.level-badge {
    font-size: 20rpx;
    padding: 2rpx 12rpx;
    border-radius: 6rpx;
    margin-left: 12rpx;
    font-weight: 400;
}
.level-badge.lv4 {
    background: #FFF3D6;
    color: #B8860B;
}
.level-badge.lv3 {
    background: #EEF0F3;
    color: #6B7280;
}
.level-badge.lv2 {
    background: #F5E6D8;
    color: #B05A2A;
}
.level-badge.lv1 {
    background: #E6F7F0;
    color: #00B578;
}
.coach-meta {
    margin: 12rpx 0;
    font-size: 24rpx;
    color: #6B7280;
}
.star {
    color: #FF9500;
}
.dot {
    color: #C0C4CC;
    margin: 0 8rpx;
}
.coach-bio {
    font-size: 22rpx;
    color: #9CA3AF;
}
.coach-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    justify-content: space-between;
    margin-left: 16rpx;
    flex-shrink: 0;
}
.select-btn {
    background: #00B578;
    color: #fff;
    font-size: 24rpx;
    padding: 8rpx 28rpx;
    border-radius: 999rpx;
    font-weight: 600;
}
</style>
