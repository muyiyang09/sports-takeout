<template>
    <view class="page">
        <view class="form card">
            <view class="form-item">
                <text class="label">联系人</text>
                <input class="input" v-model="form.consignee" placeholder="请输入联系人" />
            </view>
            <view class="form-item">
                <text class="label">手机号</text>
                <input class="input" v-model="form.phone" type="number" placeholder="请输入手机号" />
            </view>
            <view class="form-item">
                <text class="label">性别</text>
                <picker :range="['女', '男']" @change="onSexChange">
                    <view class="input">{{ form.sex === '1' ? '男' : '女' }}</view>
                </picker>
            </view>
            <view class="form-item">
                <text class="label">省</text>
                <input class="input" v-model="form.provinceName" placeholder="如 北京市" />
            </view>
            <view class="form-item">
                <text class="label">市</text>
                <input class="input" v-model="form.cityName" placeholder="如 北京市" />
            </view>
            <view class="form-item">
                <text class="label">区</text>
                <input class="input" v-model="form.districtName" placeholder="如 朝阳区" />
            </view>
            <view class="form-item">
                <text class="label">详细地址</text>
                <input class="input" v-model="form.detail" placeholder="街道、小区、门牌号" />
            </view>
            <view class="form-item">
                <text class="label">标签</text>
                <picker :range="['家', '公司', '其他']" @change="onLabelChange">
                    <view class="input">{{ form.label || '家' }}</view>
                </picker>
            </view>
            <view class="form-item">
                <text class="label">设为默认</text>
                <switch :checked="form.isDefault === 1" @change="onDefaultChange" color="#00B578" />
            </view>
        </view>

        <button class="save-btn" @tap="save">保存</button>
    </view>
</template>

<script>
const api = require('../../api/index.js');

export default {
    data() {
        return {
            form: {
                id: null,
                consignee: '',
                phone: '',
                sex: '0',
                provinceName: '',
                provinceCode: '',
                cityName: '',
                cityCode: '',
                districtName: '',
                districtCode: '',
                detail: '',
                label: '家',
                isDefault: 0
            }
        };
    },
    onLoad() {
        const edit = uni.getStorageSync('editAddress');
        if (edit) {
            this.form = Object.assign(this.form, edit);
        }
    },
    methods: {
        onSexChange(e) {
            this.form.sex = String(e.detail.value);
        },
        onLabelChange(e) {
            const labels = ['家', '公司', '其他'];
            this.form.label = labels[e.detail.value];
        },
        onDefaultChange(e) {
            this.form.isDefault = e.detail.value ? 1 : 0;
        },
        async save() {
            if (!this.form.consignee || !this.form.phone || !this.form.detail) {
                uni.showToast({ title: '请填写完整信息', icon: 'none' });
                return;
            }
            try {
                if (this.form.id) {
                    await api.updateAddress(this.form);
                } else {
                    await api.saveAddress(this.form);
                }
                uni.showToast({ title: '保存成功', icon: 'success' });
                setTimeout(() => {
                    uni.navigateBack();
                }, 600);
            } catch (e) {}
        }
    }
};
</script>

<style>
.page {
    padding: 20rpx;
}
.form {
    padding: 0 28rpx;
}
.form-item {
    display: flex;
    align-items: center;
    padding: 28rpx 0;
    border-bottom: 1rpx solid #EEF0F3;
}
.label {
    width: 160rpx;
    font-size: 28rpx;
    color: #1A1D21;
    flex-shrink: 0;
}
.input {
    flex: 1;
    font-size: 28rpx;
}
.save-btn {
    margin-top: 40rpx;
    background: #00B578;
    color: #fff;
    font-size: 30rpx;
    border-radius: 999rpx;
    line-height: 84rpx;
    font-weight: 600;
}
</style>
