<template>
    <view class="page">
        <view class="card">
            <view class="order-info">
                <text class="order-course">{{ order.orderDishes || '上门私教服务' }}</text>
                <text class="order-meta">{{ order.scheduleDate }} {{ order.timeSlot }}</text>
            </view>
        </view>

        <view class="card">
            <view class="card-title">教练评分</view>
            <view class="star-row">
                <text
                    v-for="n in 5"
                    :key="n"
                    class="star"
                    :class="{ active: n <= coachRating }"
                    @tap="coachRating = n"
                >★</text>
            </view>
        </view>

        <view class="card">
            <view class="card-title">课程评分</view>
            <view class="star-row">
                <text
                    v-for="n in 5"
                    :key="n"
                    class="star"
                    :class="{ active: n <= courseRating }"
                    @tap="courseRating = n"
                >★</text>
            </view>
        </view>

        <view class="card">
            <view class="card-title">评价内容</view>
            <textarea class="content-input" v-model="content" placeholder="说说这次体验吧" maxlength="200" />
        </view>

        <button class="submit-btn" :class="{ 'btn-disabled': submitting }" :disabled="submitting" @tap="submit">
            {{ submitting ? '提交中...' : '提交评价' }}
        </button>
    </view>
</template>

<script>
const api = require('../../api/index.js');

export default {
    data() {
        return {
            orderId: null,
            order: {},
            coachRating: 5,
            courseRating: 5,
            content: '',
            submitting: false
        };
    },
    onLoad(options) {
        this.orderId = options.orderId;
        this.order = uni.getStorageSync('reviewOrder') || {};
    },
    methods: {
        async submit() {
            if (this.submitting) return;
            this.submitting = true;
            try {
                await api.submitReview({
                    orderId: this.orderId,
                    coachRating: this.coachRating,
                    courseRating: this.courseRating,
                    content: this.content,
                    images: null
                });
                uni.showToast({ title: '评价成功', icon: 'success' });
                setTimeout(() => {
                    uni.navigateBack();
                }, 600);
            } catch (e) {
                this.submitting = false;
            }
        }
    }
};
</script>

<style>
.page {
    padding: 20rpx;
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
.order-info {
    display: flex;
    flex-direction: column;
}
.order-course {
    font-size: 30rpx;
    font-weight: 600;
}
.order-meta {
    font-size: 24rpx;
    color: #9CA3AF;
    margin-top: 8rpx;
}
.star-row {
    display: flex;
}
.star {
    font-size: 56rpx;
    color: #E5E7EB;
    margin-right: 20rpx;
}
.star.active {
    color: #FF9500;
}
.content-input {
    width: 100%;
    height: 200rpx;
    font-size: 28rpx;
}
.submit-btn {
    background: #00B578;
    color: #fff;
    font-size: 30rpx;
    border-radius: 999rpx;
    line-height: 84rpx;
    font-weight: 600;
}
</style>
