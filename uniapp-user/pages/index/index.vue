<template>
    <view class="page">
        <!-- 品牌头 -->
        <view class="hero">
            <view class="hero-title">把健身房搬到家里</view>
            <view class="hero-sub">教练带器械上门 · 科学减脂</view>
            <view class="hero-pills">
                <text class="hero-pill">一对一私教</text>
                <text class="hero-pill">专业认证</text>
            </view>
        </view>

        <view class="body">
            <!-- 左侧分类 -->
            <scroll-view class="cate-list" scroll-y>
                <view
                    v-for="item in categories"
                    :key="item.id"
                    class="cate-item"
                    :class="{ active: activeCategoryId === item.id }"
                    @tap="switchCategory(item)"
                >
                    <view class="cate-dot" v-if="activeCategoryId === item.id"></view>
                    {{ item.name }}
                </view>
            </scroll-view>

            <!-- 右侧课程 -->
            <scroll-view class="course-list" scroll-y>
                <view v-if="courses.length === 0" class="empty">
                    <text class="empty-icon">🏃</text>
                    <text class="empty-text">该分类下暂无课程</text>
                </view>

                <view v-for="item in courses" :key="item.id" class="course-card card" @tap="goCoach(item)">
                    <view class="course-info">
                        <view class="course-name">{{ item.name }}</view>
                        <view class="course-tags">
                            <text class="tag">{{ item.intensity }}</text>
                            <text class="tag">{{ item.durationMin }}分钟</text>
                        </view>
                        <view class="course-desc text-overflow">{{ item.description }}</view>
                        <view class="course-equip text-overflow">器械：{{ item.equipment || '无需器械' }}</view>
                    </view>
                    <view class="course-right">
                        <view class="price">¥{{ item.price }}</view>
                        <view class="go-btn">去预约</view>
                    </view>
                </view>
            </scroll-view>
        </view>
    </view>
</template>

<script>
const api = require('../../api/index.js');

export default {
    data() {
        return {
            categories: [],
            courses: [],
            activeCategoryId: null
        };
    },
    onLoad() {
        this.loadCategories();
    },
    methods: {
        async loadCategories() {
            try {
                const list = await api.getCategoryList(1);
                this.categories = list || [];
                if (this.categories.length > 0) {
                    this.switchCategory(this.categories[0]);
                }
            } catch (e) {}
        },
        async switchCategory(item) {
            if (item.id === this.activeCategoryId) return;
            this.activeCategoryId = item.id;
            this.courses = [];
            try {
                const list = await api.getCourseList(item.id);
                this.courses = list || [];
            } catch (e) {}
        },
        goCoach(course) {
            uni.setStorageSync('bookingCourse', course);
            uni.navigateTo({ url: '/pages/coach/coach' });
        }
    }
};
</script>

<style>
.page {
    display: flex;
    flex-direction: column;
    height: 100vh;
}

/* 品牌头 */
.hero {
    padding: 40rpx 32rpx 32rpx;
    background: linear-gradient(150deg, #00B578 0%, #00C48A 100%);
    position: relative;
    overflow: hidden;
}
.hero::after {
    content: '';
    position: absolute;
    right: -60rpx;
    top: -80rpx;
    width: 300rpx;
    height: 300rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
}
.hero-title {
    color: #FFFFFF;
    font-size: 40rpx;
    font-weight: 700;
    letter-spacing: 1rpx;
}
.hero-sub {
    color: rgba(255, 255, 255, 0.85);
    font-size: 24rpx;
    margin-top: 12rpx;
}
.hero-pills {
    margin-top: 24rpx;
    display: flex;
    gap: 12rpx;
}
.hero-pill {
    color: #FFFFFF;
    font-size: 20rpx;
    padding: 6rpx 20rpx;
    border-radius: 999rpx;
    background: rgba(255, 255, 255, 0.18);
}

/* 主体 */
.body {
    flex: 1;
    display: flex;
    overflow: hidden;
}
.cate-list {
    width: 176rpx;
    background: #FFFFFF;
    height: 100%;
    padding: 12rpx 0;
}
.cate-item {
    position: relative;
    padding: 30rpx 20rpx;
    font-size: 26rpx;
    color: var(--text-2);
    text-align: center;
}
.cate-item.active {
    color: var(--text-1);
    font-weight: 600;
    background: var(--bg);
}
.cate-dot {
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 6rpx;
    height: 36rpx;
    border-radius: 0 6rpx 6rpx 0;
    background: var(--accent);
}

.course-list {
    flex: 1;
    height: 100%;
    padding: 20rpx;
    box-sizing: border-box;
}
.course-card {
    display: flex;
    justify-content: space-between;
    margin-bottom: 20rpx;
}
.course-info {
    flex: 1;
    min-width: 0;
}
.course-name {
    font-size: 30rpx;
    font-weight: 600;
    margin-bottom: 14rpx;
}
.course-tags {
    display: flex;
    gap: 12rpx;
    margin-bottom: 14rpx;
}
.course-desc {
    font-size: 24rpx;
    color: var(--text-2);
    margin-bottom: 10rpx;
}
.course-equip {
    font-size: 22rpx;
    color: var(--text-3);
}
.course-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    justify-content: space-between;
    margin-left: 20rpx;
    flex-shrink: 0;
}
.go-btn {
    background: var(--accent);
    color: #FFFFFF;
    font-size: 24rpx;
    padding: 10rpx 28rpx;
    border-radius: 999rpx;
    font-weight: 600;
}
</style>
