<template>
    <div>
        <!-- 统计卡片 -->
        <el-row :gutter="16" class="stat-row">
            <el-col :span="8">
                <el-card shadow="hover">
                    <div class="stat-card pending">
                        <div class="stat-num">{{ stats.pending }}</div>
                        <div class="stat-label">待派单</div>
                    </div>
                </el-card>
            </el-col>
            <el-col :span="8">
                <el-card shadow="hover">
                    <div class="stat-card dispatched">
                        <div class="stat-num">{{ stats.dispatched }}</div>
                        <div class="stat-label">已派单</div>
                    </div>
                </el-card>
            </el-col>
            <el-col :span="8">
                <el-card shadow="hover">
                    <div class="stat-card expired">
                        <div class="stat-num">{{ stats.expired }}</div>
                        <div class="stat-label">已超时</div>
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <el-card style="margin-top: 16px">
            <div class="toolbar">
                <el-select v-model="statusFilter" placeholder="派单状态" clearable style="width: 140px" @change="load">
                    <el-option label="待派单" :value="0" />
                    <el-option label="已派单" :value="1" />
                    <el-option label="已取消" :value="2" />
                </el-select>
                <el-input v-model="cityCode" placeholder="城市编码" clearable style="width: 140px" @keyup.enter="load" />
                <el-button type="primary" @click="load">查询</el-button>
                <el-button @click="load">刷新</el-button>
            </div>

            <el-table :data="list" v-loading="loading" border>
                <el-table-column prop="id" label="ID" width="60" />
                <el-table-column prop="orderNumber" label="订单号" width="200" show-overflow-tooltip />
                <el-table-column label="状态" width="90">
                    <template #default="{ row }">
                        <el-tag :type="statusTagType(row.status)">{{ statusText(row.status) }}</el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="派单类型" width="90">
                    <template #default="{ row }">{{ dispatchTypeText(row.dispatchType) }}</template>
                </el-table-column>
                <el-table-column prop="consignee" label="联系人" width="90" />
                <el-table-column prop="phone" label="手机号" width="120" />
                <el-table-column prop="cityCode" label="城市" width="80" />
                <el-table-column prop="scheduleDate" label="上门日期" width="110" />
                <el-table-column prop="timeSlot" label="时段" width="120" />
                <el-table-column prop="address" label="地址" min-width="160" show-overflow-tooltip />
                <el-table-column prop="amount" label="金额" width="80" />
                <el-table-column label="超时时间" width="160">
                    <template #default="{ row }">
                        <span :class="{ 'text-danger': isExpired(row) }">{{ formatTime(row.expireTime) }}</span>
                    </template>
                </el-table-column>
                <el-table-column label="教练ID" width="80">
                    <template #default="{ row }">{{ row.coachId || '-' }}</template>
                </el-table-column>
                <el-table-column label="派单时间" width="160">
                    <template #default="{ row }">{{ formatTime(row.dispatchTime) }}</template>
                </el-table-column>
            </el-table>
        </el-card>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import api from '../api';

const list = ref([]);
const loading = ref(false);
const statusFilter = ref(null);
const cityCode = ref('');

const statusMap = { 0: '待派单', 1: '已派单', 2: '已取消' };
const dispatchTypeMap = { 0: '待派', 1: '系统派', 2: '教练抢单' };

function statusText(s) {
    return statusMap[s] ?? '未知';
}
function statusTagType(s) {
    return s === 0 ? 'warning' : s === 1 ? 'success' : 'info';
}
function dispatchTypeText(t) {
    return dispatchTypeMap[t] ?? '-';
}

const stats = computed(() => {
    const now = new Date();
    let pending = 0, dispatched = 0, expired = 0;
    list.value.forEach((item) => {
        if (item.status === 0) {
            // 判断是否超时
            if (item.expireTime && new Date(item.expireTime) < now) {
                expired++;
            } else {
                pending++;
            }
        } else if (item.status === 1) {
            dispatched++;
        }
    });
    return { pending, dispatched, expired };
});

function isExpired(row) {
    if (row.status !== 0 || !row.expireTime) return false;
    return new Date(row.expireTime) < new Date();
}

function formatTime(t) {
    if (!t) return '-';
    return t.replace('T', ' ').substring(0, 16);
}

async function load() {
    loading.value = true;
    try {
        const data = await api.get('/admin/dispatchPool/list', {
            status: statusFilter.value,
            cityCode: cityCode.value
        });
        list.value = data || [];
    } catch (e) {
        ElMessage.error(e.message);
    } finally {
        loading.value = false;
    }
}

onMounted(load);
</script>

<style scoped>
.stat-row {
    margin-bottom: 0;
}
.stat-card {
    text-align: center;
    padding: 12px 0;
}
.stat-num {
    font-size: 32px;
    font-weight: bold;
}
.stat-label {
    color: #909399;
    font-size: 14px;
    margin-top: 4px;
}
.stat-card.pending .stat-num {
    color: #e6a23c;
}
.stat-card.dispatched .stat-num {
    color: #67c23a;
}
.stat-card.expired .stat-num {
    color: #f56c6c;
}
.toolbar {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
}
.text-danger {
    color: #f56c6c;
}
</style>
