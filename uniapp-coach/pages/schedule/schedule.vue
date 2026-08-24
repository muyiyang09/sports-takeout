<template>
    <view class="page">
        <!-- 生成排期 -->
        <view class="card">
            <view class="card-title">生成排期</view>
            <view class="row">
                <text class="label">开始日期</text>
                <picker mode="date" :value="startDate" @change="onStartChange">
                    <view class="picker">{{ startDate }}</view>
                </picker>
            </view>
            <view class="row">
                <text class="label">结束日期</text>
                <picker mode="date" :value="endDate" @change="onEndChange">
                    <view class="picker">{{ endDate }}</view>
                </picker>
            </view>
            <view class="row">
                <text class="label">选择时段</text>
            </view>
            <view class="slot-grid">
                <view
                    v-for="s in stdSlots"
                    :key="s"
                    class="slot-item"
                    :class="{ selected: selectedSlots.indexOf(s) >= 0 }"
                    @tap="toggleSlot(s)"
                >
                    {{ s }}
                </view>
            </view>
            <button class="gen-btn" @tap="generate">生成排期</button>
        </view>

        <!-- 现有排期 -->
        <view class="card">
            <view class="card-title">我的排期</view>
            <view v-if="schedules.length === 0" class="empty">
                <text class="empty-icon">🗓️</text>
                <text class="empty-text">暂无排期</text>
                <text class="empty-sub">生成排期后用户才能约你</text>
            </view>
            <view v-for="item in schedules" :key="item.id" class="schedule-item">
                <text>{{ item.scheduleDate }} {{ item.timeSlot }}</text>
                <text class="sched-status" :class="'s' + item.status">{{ statusText(item.status) }}</text>
            </view>
        </view>
    </view>
</template>

<script>
const api = require('../../api/index.js');

export default {
    data() {
        return {
            startDate: '',
            endDate: '',
            stdSlots: ['09:00-10:00', '10:00-11:00', '11:00-12:00', '14:00-15:00', '15:00-16:00', '16:00-17:00', '17:00-18:00', '18:00-19:00', '19:00-20:00'],
            selectedSlots: [],
            schedules: []
        };
    },
    onLoad() {
        const now = new Date();
        this.startDate = this.fmt(now);
        const end = new Date(now.getTime() + 6 * 24 * 3600 * 1000);
        this.endDate = this.fmt(end);
        this.loadSchedule();
    },
    methods: {
        fmt(d) {
            const y = d.getFullYear();
            const m = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            return y + '-' + m + '-' + day;
        },
        onStartChange(e) {
            this.startDate = e.detail.value;
        },
        onEndChange(e) {
            this.endDate = e.detail.value;
        },
        toggleSlot(s) {
            const idx = this.selectedSlots.indexOf(s);
            if (idx >= 0) {
                this.selectedSlots.splice(idx, 1);
            } else {
                this.selectedSlots.push(s);
            }
        },
        statusText(s) {
            return { 1: '可约', 2: '已占', 3: '休息' }[s] || '未知';
        },
        async loadSchedule() {
            try {
                this.schedules = await api.getSchedule(this.startDate, this.endDate) || [];
            } catch (e) {}
        },
        async generate() {
            if (this.selectedSlots.length === 0) {
                uni.showToast({ title: '请选择时段', icon: 'none' });
                return;
            }
            try {
                await api.generateSchedule({
                    startDate: this.startDate,
                    endDate: this.endDate,
                    timeSlots: this.selectedSlots
                });
                uni.showToast({ title: '排期已生成', icon: 'success' });
                this.loadSchedule();
            } catch (e) {}
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
.row {
    display: flex;
    align-items: center;
    margin-bottom: 20rpx;
    font-size: 28rpx;
}
.label {
    color: #6B7280;
    width: 160rpx;
}
.picker {
    color: #2F80ED;
}
.slot-grid {
    display: flex;
    flex-wrap: wrap;
    margin-bottom: 20rpx;
}
.slot-item {
    width: 30%;
    padding: 18rpx 0;
    text-align: center;
    background: #F6F7F9;
    border-radius: 12rpx;
    margin-right: 3%;
    margin-bottom: 14rpx;
    font-size: 24rpx;
    color: #1A1D21;
}
.slot-item.selected {
    background: #2F80ED;
    color: #fff;
    font-weight: 600;
}
.gen-btn {
    background: #2F80ED;
    color: #fff;
    font-size: 28rpx;
    border-radius: 999rpx;
    line-height: 76rpx;
    font-weight: 600;
}
.schedule-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20rpx 0;
    border-bottom: 1rpx solid #EEF0F3;
    font-size: 26rpx;
}
.sched-status {
    font-size: 22rpx;
}
.sched-status.s1 {
    color: #00B578;
}
.sched-status.s2 {
    color: #FF6B35;
}
.sched-status.s3 {
    color: #9CA3AF;
}
</style>
