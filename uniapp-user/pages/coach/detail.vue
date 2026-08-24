<template>
    <view class="page">
        <!-- 教练信息 -->
        <view class="coach-header card">
            <view class="avatar">{{ firstChar(coach.name) }}</view>
            <view class="coach-info">
                <view class="coach-name">{{ coach.name }}</view>
                <view class="coach-meta">
                    <text class="star">★ {{ coach.rating }}</text>
                    <text class="dot">·</text>
                    <text>{{ coach.serviceRadiusKm }}km</text>
                    <text class="dot">·</text>
                    <text>{{ coach.cityName }}</text>
                </view>
                <view class="coach-bio">{{ coach.bio }}</view>
                <view v-if="coach.certificates && coach.certificates.length" class="certs">
                    <text v-for="c in coach.certificates" :key="c.id" class="cert">{{ c.certType }}</text>
                </view>
            </view>
        </view>

        <!-- 排期选择 -->
        <view class="schedule-section card">
            <view class="section-title">选择上门时段</view>

            <scroll-view class="date-list" scroll-x>
                <view
                    v-for="(d, i) in dates"
                    :key="i"
                    class="date-item"
                    :class="{ active: activeDateIndex === i }"
                    @tap="switchDate(i)"
                >
                    <text class="date-week">{{ d.week }}</text>
                    <text class="date-day">{{ d.day }}</text>
                </view>
            </scroll-view>

            <view v-if="slots.length === 0" class="empty">
                <text class="empty-icon">🗓️</text>
                <text class="empty-text">该日期无可约时段</text>
            </view>
            <view v-else class="slot-grid">
                <view
                    v-for="s in slots"
                    :key="s.id"
                    class="slot-item"
                    :class="{ selected: selectedSlot && selectedSlot.id === s.id, disabled: s.status !== 1 }"
                    @tap="selectSlot(s)"
                >
                    {{ s.timeSlot }}
                </view>
            </view>
        </view>

        <!-- 底部预约按钮 -->
        <view class="footer">
            <view class="footer-price">¥{{ course ? course.price : '--' }}</view>
            <button class="book-btn" :class="{ 'btn-disabled': !selectedSlot }" @tap="goBooking">立即预约</button>
        </view>
    </view>
</template>

<script>
const api = require('../../api/index.js');

export default {
    data() {
        return {
            coachId: null,
            coach: {},
            course: null,
            dates: [],
            activeDateIndex: 0,
            slots: [],
            selectedSlot: null
        };
    },
    onLoad(options) {
        this.coachId = options.id;
        this.course = uni.getStorageSync('bookingCourse') || null;
        this.loadCoach();
        this.buildDates();
        this.loadSchedule(this.dates[0].value);
    },
    methods: {
        firstChar(name) {
            return (name || '').charAt(0) || '?';
        },
        async loadCoach() {
            try {
                this.coach = await api.getCoachDetail(this.coachId) || {};
            } catch (e) {}
        },
        buildDates() {
            const weeks = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
            const arr = [];
            for (let i = 0; i < 7; i++) {
                const d = new Date();
                d.setDate(d.getDate() + i);
                const value = this.formatDate(d);
                arr.push({
                    value,
                    week: i === 0 ? '今天' : weeks[d.getDay()],
                    day: String(d.getMonth() + 1) + '-' + String(d.getDate())
                });
            }
            this.dates = arr;
        },
        formatDate(d) {
            const y = d.getFullYear();
            const m = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            return y + '-' + m + '-' + day;
        },
        async switchDate(i) {
            this.activeDateIndex = i;
            this.selectedSlot = null;
            this.slots = [];
            await this.loadSchedule(this.dates[i].value);
        },
        async loadSchedule(date) {
            try {
                this.slots = await api.getCoachSchedule(this.coachId, date) || [];
            } catch (e) {}
        },
        selectSlot(s) {
            if (s.status !== 1) return;
            this.selectedSlot = s;
        },
        goBooking() {
            if (!this.selectedSlot) {
                uni.showToast({ title: '请选择时段', icon: 'none' });
                return;
            }
            uni.setStorageSync('bookingCoach', this.coach);
            uni.setStorageSync('bookingSchedule', this.selectedSlot);
            uni.navigateTo({ url: '/pages/booking/booking?mode=appoint' });
        }
    }
};
</script>

<style>
.page {
    padding: 20rpx;
    padding-bottom: 160rpx;
}
.coach-header {
    display: flex;
    margin-bottom: 20rpx;
}
.avatar {
    width: 120rpx;
    height: 120rpx;
    border-radius: 50%;
    background: #00B578;
    color: #fff;
    font-size: 48rpx;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 24rpx;
    flex-shrink: 0;
}
.coach-info {
    flex: 1;
    min-width: 0;
}
.coach-name {
    font-size: 34rpx;
    font-weight: 600;
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
    font-size: 24rpx;
    color: #6B7280;
}
.certs {
    margin-top: 12rpx;
}
.cert {
    display: inline-block;
    background: #E6F7F0;
    color: #00B578;
    font-size: 20rpx;
    padding: 4rpx 12rpx;
    border-radius: 6rpx;
    margin-right: 12rpx;
}
.schedule-section {
    padding: 28rpx;
}
.section-title {
    font-size: 30rpx;
    font-weight: 600;
    margin-bottom: 24rpx;
}
.date-list {
    white-space: nowrap;
    margin-bottom: 24rpx;
}
.date-item {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    padding: 14rpx 24rpx;
    border-radius: 12rpx;
    margin-right: 16rpx;
    background: #F6F7F9;
}
.date-item.active {
    background: #E6F7F0;
}
.date-week {
    font-size: 22rpx;
    color: #9CA3AF;
}
.date-day {
    font-size: 26rpx;
    font-weight: 600;
    margin-top: 6rpx;
}
.slot-grid {
    display: flex;
    flex-wrap: wrap;
}
.slot-item {
    width: 30%;
    padding: 20rpx 0;
    text-align: center;
    background: #F6F7F9;
    border-radius: 12rpx;
    margin-right: 3%;
    margin-bottom: 16rpx;
    font-size: 24rpx;
    color: #1A1D21;
}
.slot-item.selected {
    background: #00B578;
    color: #fff;
    font-weight: 600;
}
.slot-item.disabled {
    color: #C0C4CC;
    background: #FBFBFC;
}
.footer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #fff;
    padding: 20rpx 32rpx;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 -2rpx 12rpx rgba(17, 24, 39, 0.06);
}
.footer-price {
    color: #FF6B35;
    font-size: 36rpx;
    font-weight: 600;
}
.book-btn {
    background: #00B578;
    color: #fff;
    font-size: 28rpx;
    padding: 0 60rpx;
    border-radius: 999rpx;
    line-height: 72rpx;
    font-weight: 600;
}
</style>
