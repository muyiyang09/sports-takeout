<template>
    <view class="page">
        <view class="form">
            <!-- 头像上传 -->
            <view class="form-item avatar-item">
                <text class="label">头像</text>
                <view class="avatar-box" @tap="chooseAvatar">
                    <image v-if="avatarPreview" class="avatar-img" :src="avatarPreview" mode="aspectFill" />
                    <view v-else class="avatar-placeholder">+</view>
                </view>
                <text class="avatar-tip">点击上传</text>
            </view>

            <view class="form-item">
                <text class="label">姓名</text>
                <input class="input" v-model="form.name" placeholder="请输入姓名" />
            </view>
            <view class="form-item">
                <text class="label">手机号</text>
                <input class="input" v-model="form.phone" type="number" placeholder="请输入手机号" />
            </view>
            <view class="form-item">
                <text class="label">密码</text>
                <input class="input" v-model="form.password" password placeholder="请输入密码" />
            </view>
            <view class="form-item">
                <text class="label">性别</text>
                <picker :range="['女', '男']" @change="onSexChange">
                    <view class="input">{{ form.sex === '1' ? '男' : '女' }}</view>
                </picker>
            </view>
            <view class="form-item">
                <text class="label">等级</text>
                <picker :range="['初级', '中级', '高级', '金牌']" @change="onLevelChange">
                    <view class="input">{{ levelLabel }}</view>
                </picker>
            </view>
            <view class="form-item">
                <text class="label">服务半径(km)</text>
                <input class="input" type="digit" v-model="form.serviceRadiusKm" placeholder="如 5" />
            </view>
            <view class="form-item">
                <text class="label">服务城市</text>
                <input class="input" v-model="form.cityName" placeholder="如 北京市" />
            </view>
            <view class="form-item">
                <text class="label">证书类型</text>
                <input class="input" v-model="certType" placeholder="如 国职/ACE/NASM" />
            </view>
            <view class="form-item">
                <text class="label">证书编号</text>
                <input class="input" v-model="certNo" placeholder="选填" />
            </view>
            <view class="form-item">
                <text class="label">简介/擅长</text>
                <textarea class="textarea" v-model="form.bio" placeholder="介绍你的专业方向与经验" />
            </view>
        </view>

        <button class="submit-btn" :class="{ 'btn-disabled': submitting }" :disabled="submitting" @tap="doRegister">
            {{ submitting ? '提交中...' : '提交入驻' }}
        </button>
        <view class="tip">提交后需平台审核，审核通过后可接单</view>
    </view>
</template>

<script>
const api = require('../../api/index.js');
const { fullUrl } = require('../../api/request.js');

export default {
    data() {
        return {
            form: {
                name: '',
                phone: '',
                password: '',
                sex: '1',
                avatar: '',
                level: 1,
                serviceRadiusKm: 5,
                cityCode: '110100',
                cityName: '北京市',
                bio: '',
                certificates: []
            },
            avatarPreview: '',
            certType: '',
            certNo: '',
            submitting: false
        };
    },
    computed: {
        levelLabel() {
            const map = { 1: '初级', 2: '中级', 3: '高级', 4: '金牌' };
            return map[this.form.level] || '初级';
        }
    },
    methods: {
        onSexChange(e) {
            this.form.sex = String(e.detail.value);
        },
        onLevelChange(e) {
            this.form.level = e.detail.value + 1;
        },
        chooseAvatar() {
            uni.chooseImage({
                count: 1,
                sizeType: ['compressed'],
                success: async (res) => {
                    const path = res.tempFilePaths[0];
                    try {
                        const url = await api.uploadAvatar(path);
                        this.form.avatar = url;
                        this.avatarPreview = fullUrl(url);
                        uni.showToast({ title: '头像已上传', icon: 'none' });
                    } catch (e) {}
                }
            });
        },
        buildCertificates() {
            if (this.certType || this.certNo) {
                return [{
                    certType: this.certType,
                    certNo: this.certNo,
                    status: 0
                }];
            }
            return [];
        },
        async doRegister() {
            if (!this.form.name || !this.form.phone || !this.form.password) {
                uni.showToast({ title: '请填写姓名/手机号/密码', icon: 'none' });
                return;
            }
            this.submitting = true;
            try {
                const data = Object.assign({}, this.form, {
                    serviceRadiusKm: Number(this.form.serviceRadiusKm),
                    certificates: this.buildCertificates()
                });
                await api.register(data);
                uni.showToast({ title: '提交成功，待审核', icon: 'success' });
                setTimeout(() => {
                    uni.navigateBack();
                }, 800);
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
    padding-bottom: 60rpx;
}
.form {
    background: #fff;
    border-radius: 16rpx;
    padding: 0 28rpx;
}
.form-item {
    display: flex;
    align-items: center;
    padding: 28rpx 0;
    border-bottom: 1rpx solid #f2f3f5;
}
.avatar-item {
    align-items: center;
}
.label {
    width: 200rpx;
    font-size: 28rpx;
    color: #333;
}
.input {
    flex: 1;
    font-size: 28rpx;
}
.textarea {
    flex: 1;
    height: 140rpx;
    font-size: 28rpx;
}
.avatar-box {
    width: 100rpx;
    height: 100rpx;
    border-radius: 50%;
    overflow: hidden;
    background: #f2f3f5;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 20rpx;
}
.avatar-img {
    width: 100%;
    height: 100%;
}
.avatar-placeholder {
    font-size: 56rpx;
    color: #c0c4cc;
    line-height: 1;
}
.avatar-tip {
    font-size: 24rpx;
    color: #2F80ED;
}
.submit-btn {
    margin-top: 40rpx;
    background: #2F80ED;
    color: #fff;
    font-size: 30rpx;
    border-radius: 44rpx;
    line-height: 84rpx;
}
.tip {
    text-align: center;
    color: #999;
    font-size: 22rpx;
    margin-top: 20rpx;
}
</style>
