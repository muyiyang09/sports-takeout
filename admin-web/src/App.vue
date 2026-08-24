<template>
    <LoginView v-if="!loggedIn" @success="onLogin" />

    <el-container v-else class="layout">
        <el-aside width="200px" class="aside">
            <div class="logo">体育外卖 · 管理端</div>
            <el-menu :default-active="active" background-color="#001529" text-color="#c0c4cc" active-text-color="#409eff" @select="onSelect">
                <el-menu-item index="coach">教练审核</el-menu-item>
                <el-menu-item index="course">课程管理</el-menu-item>
                <el-menu-item index="order">订单管理</el-menu-item>
                <el-menu-item index="dispatchPool">派单池监控</el-menu-item>
            </el-menu>
            <div class="logout" @click="logout">退出登录</div>
        </el-aside>

        <el-main class="main">
            <CoachView v-if="active === 'coach'" />
            <CourseView v-else-if="active === 'course'" />
            <OrderView v-else-if="active === 'order'" />
            <DispatchPoolView v-else />
        </el-main>
    </el-container>
</template>

<script setup>
import { ref } from 'vue';
import { getToken, clearToken } from './api.js';
import LoginView from './views/LoginView.vue';
import CoachView from './views/CoachView.vue';
import CourseView from './views/CourseView.vue';
import OrderView from './views/OrderView.vue';
import DispatchPoolView from './views/DispatchPoolView.vue';

const loggedIn = ref(!!getToken());
const active = ref('coach');

function onLogin() {
    loggedIn.value = true;
    active.value = 'coach';
}

function onSelect(index) {
    active.value = index;
}

function logout() {
    clearToken();
    loggedIn.value = false;
}
</script>

<style>
html,
body,
#app {
    height: 100%;
    margin: 0;
    font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}
.layout {
    height: 100%;
}
.aside {
    background: #001529;
    display: flex;
    flex-direction: column;
}
.logo {
    color: #fff;
    font-size: 16px;
    font-weight: bold;
    padding: 20px 16px;
    text-align: center;
}
.el-menu {
    border-right: none;
    flex: 1;
}
.logout {
    color: #c0c4cc;
    text-align: center;
    padding: 16px;
    cursor: pointer;
    font-size: 14px;
}
.main {
    background: #f0f2f5;
    padding: 20px;
}
</style>
