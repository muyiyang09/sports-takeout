<template>
    <view class="page">
        <view v-if="list.length === 0" class="empty">
            <text class="empty-icon">📍</text>
            <text class="empty-text">暂无地址</text>
            <text class="empty-sub">添加上门地址后即可预约</text>
        </view>

        <view v-for="item in list" :key="item.id" class="addr-card card" @tap="select(item)">
            <view class="addr-info">
                <view class="addr-name">
                    {{ item.consignee }} {{ item.phone }}
                    <text v-if="item.isDefault === 1" class="default-tag">默认</text>
                </view>
                <view class="addr-detail">{{ item.provinceName }}{{ item.cityName }}{{ item.districtName }}{{ item.detail }}</view>
            </view>
            <view class="addr-actions" @tap.stop>
                <text class="act" @tap="edit(item)">编辑</text>
                <text v-if="item.isDefault !== 1" class="act" @tap="setDefault(item)">设为默认</text>
                <text class="act del" @tap="remove(item)">删除</text>
            </view>
        </view>

        <button class="add-btn" @tap="add">新增地址</button>
    </view>
</template>

<script>
const api = require('../../api/index.js');

export default {
    data() {
        return {
            list: [],
            pick: false
        };
    },
    onLoad(options) {
        this.pick = options.pick === '1';
    },
    onShow() {
        this.loadList();
    },
    methods: {
        async loadList() {
            try {
                this.list = await api.getAddressList() || [];
            } catch (e) {}
        },
        select(item) {
            if (this.pick) {
                uni.setStorageSync('bookingAddress', item);
                uni.navigateBack();
            }
        },
        add() {
            uni.navigateTo({ url: '/pages/address/edit' });
        },
        edit(item) {
            uni.setStorageSync('editAddress', item);
            uni.navigateTo({ url: '/pages/address/edit' });
        },
        async setDefault(item) {
            try {
                await api.setDefaultAddress({ id: item.id });
                this.loadList();
            } catch (e) {}
        },
        async remove(item) {
            uni.showModal({
                title: '提示',
                content: '确认删除该地址吗？',
                success: async (res) => {
                    if (res.confirm) {
                        try {
                            await api.deleteAddress(item.id);
                            uni.showToast({ title: '已删除', icon: 'none' });
                            this.loadList();
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
    padding-bottom: 160rpx;
}
.addr-card {
    margin-bottom: 20rpx;
}
.addr-name {
    font-size: 30rpx;
    font-weight: 600;
}
.default-tag {
    background: #E6F7F0;
    color: #00B578;
    font-size: 20rpx;
    padding: 2rpx 12rpx;
    border-radius: 6rpx;
    margin-left: 12rpx;
}
.addr-detail {
    font-size: 24rpx;
    color: #6B7280;
    margin-top: 10rpx;
}
.addr-actions {
    display: flex;
    justify-content: flex-end;
    margin-top: 16rpx;
}
.act {
    font-size: 24rpx;
    color: #00B578;
    margin-left: 28rpx;
}
.act.del {
    color: #FF6B35;
}
.add-btn {
    position: fixed;
    bottom: 30rpx;
    left: 40rpx;
    right: 40rpx;
    background: #00B578;
    color: #fff;
    font-size: 30rpx;
    border-radius: 999rpx;
    line-height: 84rpx;
    font-weight: 600;
}
</style>
