<template>
    <view class="page">
        <!-- 课程信息 -->
        <view class="card">
            <view class="course-name">{{ course.name }}</view>
            <view class="course-meta">
                <text class="tag">{{ course.intensity }}</text>
                <text class="tag">{{ course.durationMin }}分钟</text>
                <text class="price">¥{{ course.price }}</text>
            </view>
        </view>

        <!-- 教练 / 派单 -->
        <view class="card">
            <view class="card-title">服务方式</view>
            <view v-if="mode === 'appoint' && coach" class="coach-row">
                <view class="avatar">{{ firstChar(coach.name) }}</view>
                <view class="coach-name">{{ coach.name }}</view>
                <text class="star">★ {{ coach.rating }}</text>
            </view>
            <view v-else class="coach-row">
                <text class="dispatch-label">就近派单</text>
                <text class="dispatch-sub">平台就近派教练上门</text>
            </view>
        </view>

        <!-- 时段 -->
        <view class="card">
            <view class="card-title">上门时段</view>
            <!-- 指定教练：已选排期 -->
            <view v-if="mode === 'appoint' && schedule" class="slot-fixed">
                {{ schedule.scheduleDate }} {{ schedule.timeSlot }}
            </view>
            <!-- 派单：自由选日期时段 -->
            <view v-else>
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
                <view class="slot-grid">
                    <view
                        v-for="s in stdSlots"
                        :key="s"
                        class="slot-item"
                        :class="{ selected: selectedSlot === s }"
                        @tap="selectedSlot = s"
                    >
                        {{ s }}
                    </view>
                </view>
            </view>
        </view>

        <!-- 地址 -->
        <view class="card" @tap="pickAddress">
            <view class="card-title">上门地址</view>
            <view v-if="address" class="addr-row">
                <view class="addr-info">
                    <text class="addr-name">{{ address.consignee }} {{ address.phone }}</text>
                    <text class="addr-detail">{{ address.provinceName }}{{ address.cityName }}{{ address.districtName }}{{ address.detail }}</text>
                </view>
                <text class="arrow">›</text>
            </view>
            <view v-else class="addr-empty">请选择上门地址 ›</view>
        </view>

        <!-- 备注 -->
        <view class="card">
            <view class="card-title">备注</view>
            <input class="remark-input" v-model="remark" placeholder="可填写健康情况、器械需求等" />
        </view>

        <!-- 协议勾选 -->
        <view class="card agreement-card">
            <view class="agree-row" @tap="toggleAgree">
                <view class="checkbox" :class="{ checked: agreed }">
                    <text v-if="agreed" class="check">✓</text>
                </view>
                <view class="agree-text">
                    我已阅读并同意
                    <text class="link" @tap.stop="goAgreement">《上门服务免责协议》</text>
                    <text class="link" @tap.stop="goAgreement">《用户协议》</text>
                    <text class="link" @tap.stop="goAgreement">《隐私政策》</text>
                </view>
            </view>
        </view>

        <!-- 底部提交 -->
        <view class="footer">
            <view class="footer-amount">合计 <text class="price">¥{{ course.price }}</text></view>
            <button class="submit-btn" :class="{ 'btn-disabled': !canSubmit || submitting }" :disabled="!canSubmit || submitting" @tap="submit">
                {{ submitting ? '提交中...' : '提交订单并支付' }}
            </button>
        </view>
    </view>
</template>

<script>
const api = require('../../api/index.js');

export default {
    data() {
        return {
            mode: 'appoint',
            course: {},
            coach: null,
            schedule: null,
            address: null,
            remark: '',
            agreed: false,
            dates: [],
            activeDateIndex: 0,
            selectedSlot: null,
            stdSlots: ['09:00-10:00', '10:00-11:00', '11:00-12:00', '14:00-15:00', '15:00-16:00', '16:00-17:00', '17:00-18:00', '18:00-19:00', '19:00-20:00'],
            submitting: false
        };
    },
    computed: {
        canSubmit() {
            if (!this.agreed) return false;
            if (!this.address) return false;
            if (this.mode === 'appoint') {
                return !!this.schedule;
            }
            return !!this.selectedSlot;
        }
    },
    onLoad(options) {
        this.mode = options.mode || 'appoint';
        this.course = uni.getStorageSync('bookingCourse') || {};
        this.coach = uni.getStorageSync('bookingCoach') || null;
        this.schedule = uni.getStorageSync('bookingSchedule') || null;
        this.buildDates();
        this.loadDefaultAddress();
    },
    onShow() {
        // 从地址列表返回后读取选中地址
        const picked = uni.getStorageSync('bookingAddress');
        if (picked) {
            this.address = picked;
        }
    },
    methods: {
        firstChar(name) {
            return (name || '').charAt(0) || '?';
        },
        toggleAgree() {
            this.agreed = !this.agreed;
        },
        goAgreement() {
            uni.navigateTo({ url: '/pages/agreement/agreement' });
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
            this.selectedSlot = this.stdSlots[0];
        },
        formatDate(d) {
            const y = d.getFullYear();
            const m = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            return y + '-' + m + '-' + day;
        },
        switchDate(i) {
            this.activeDateIndex = i;
        },
        async loadDefaultAddress() {
            try {
                this.address = await api.getDefaultAddress();
            } catch (e) {}
        },
        pickAddress() {
            uni.navigateTo({ url: '/pages/address/address?pick=1' });
        },
        buildDetail() {
            const scheduleDate = this.mode === 'appoint' ? this.schedule.scheduleDate : this.dates[this.activeDateIndex].value;
            const timeSlot = this.mode === 'appoint' ? this.schedule.timeSlot : this.selectedSlot;
            const detail = {
                courseId: this.course.id,
                name: this.course.name,
                image: this.course.image,
                number: 1,
                amount: this.course.price,
                scheduleDate: scheduleDate,
                timeSlot: timeSlot
            };
            if (this.mode === 'appoint' && this.coach) {
                detail.coachId = this.coach.id;
                detail.coachName = this.coach.name;
                detail.scheduleId = this.schedule.id;
            }
            return [detail];
        },
        async submit() {
            if (!this.canSubmit || this.submitting) return;
            this.submitting = true;
            try {
                const dto = {
                    addressBookId: this.address.id,
                    payMethod: 1,
                    remark: this.remark,
                    amount: this.course.price,
                    orderMode: this.mode === 'appoint' ? 1 : 2,
                    dispatchType: this.mode === 'appoint' ? null : 0,
                    scheduleId: this.mode === 'appoint' ? this.schedule.id : null,
                    scheduleDate: this.mode === 'appoint' ? this.schedule.scheduleDate : this.dates[this.activeDateIndex].value,
                    timeSlot: this.mode === 'appoint' ? this.schedule.timeSlot : this.selectedSlot,
                    coachId: this.mode === 'appoint' ? this.coach.id : null,
                    orderDetails: this.buildDetail()
                };

                const submitRes = await api.submitOrder(dto);
                // 模拟支付
                await api.payOrder({ orderNumber: submitRes.orderNumber, payMethod: 1 });

                uni.showToast({ title: '下单成功', icon: 'success' });
                setTimeout(() => {
                    uni.redirectTo({ url: '/pages/order/detail?id=' + submitRes.id });
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
    padding-bottom: 160rpx;
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
.course-name {
    font-size: 32rpx;
    font-weight: bold;
}
.course-meta {
    margin-top: 16rpx;
    display: flex;
    align-items: center;
}
.tag {
    background: #e6f9f1;
    color: #00B578;
    font-size: 22rpx;
    padding: 4rpx 14rpx;
    border-radius: 6rpx;
    margin-right: 16rpx;
}
.coach-row {
    display: flex;
    align-items: center;
}
.avatar {
    width: 72rpx;
    height: 72rpx;
    border-radius: 50%;
    background: #00B578;
    color: #fff;
    font-size: 32rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 16rpx;
}
.coach-name {
    font-size: 30rpx;
    font-weight: bold;
    margin-right: 16rpx;
}
.star {
    color: #ff9500;
    font-size: 26rpx;
}
.dispatch-label {
    font-size: 30rpx;
    font-weight: bold;
    color: #00B578;
    margin-right: 16rpx;
}
.dispatch-sub {
    font-size: 24rpx;
    color: #999;
}
.slot-fixed {
    font-size: 30rpx;
    color: #00B578;
    font-weight: bold;
}
.date-list {
    white-space: nowrap;
    margin-bottom: 20rpx;
}
.date-item {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    padding: 14rpx 22rpx;
    border-radius: 12rpx;
    margin-right: 14rpx;
    background: #f2f3f5;
}
.date-item.active {
    background: #e6f9f1;
}
.date-week {
    font-size: 20rpx;
    color: #999;
}
.date-day {
    font-size: 24rpx;
    font-weight: bold;
    margin-top: 4rpx;
}
.slot-grid {
    display: flex;
    flex-wrap: wrap;
}
.slot-item {
    width: 30%;
    padding: 18rpx 0;
    text-align: center;
    background: #f2f3f5;
    border-radius: 12rpx;
    margin-right: 3%;
    margin-bottom: 14rpx;
    font-size: 24rpx;
}
.slot-item.selected {
    background: #00B578;
    color: #fff;
}
.addr-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.addr-info {
    display: flex;
    flex-direction: column;
}
.addr-name {
    font-size: 28rpx;
    font-weight: bold;
}
.addr-detail {
    font-size: 24rpx;
    color: #666;
    margin-top: 8rpx;
}
.addr-empty {
    font-size: 28rpx;
    color: #00B578;
}
.arrow {
    font-size: 40rpx;
    color: #ccc;
}
.remark-input {
    font-size: 28rpx;
}
.agreement-card {
    padding: 20rpx 28rpx;
}
.agree-row {
    display: flex;
    align-items: flex-start;
}
.checkbox {
    width: 36rpx;
    height: 36rpx;
    border-radius: 50%;
    border: 2rpx solid #ccc;
    margin-right: 16rpx;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}
.checkbox.checked {
    background: #00B578;
    border-color: #00B578;
}
.check {
    color: #fff;
    font-size: 22rpx;
    line-height: 1;
}
.agree-text {
    font-size: 24rpx;
    color: #6B7280;
    line-height: 1.6;
}
.link {
    color: #00B578;
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
    box-shadow: 0 -2rpx 10rpx rgba(0, 0, 0, 0.05);
}
.footer-amount {
    font-size: 28rpx;
}
.submit-btn {
    background: #00B578;
    color: #fff;
    font-size: 28rpx;
    padding: 0 50rpx;
    border-radius: 40rpx;
    line-height: 72rpx;
}
</style>
