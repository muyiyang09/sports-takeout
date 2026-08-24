<template>
    <div>
        <el-card>
            <div class="toolbar">
                <el-input v-model="query.number" placeholder="订单号" clearable style="width: 200px" @keyup.enter="load" />
                <el-input v-model="query.phone" placeholder="手机号" clearable style="width: 160px" @keyup.enter="load" />
                <el-select v-model="query.status" placeholder="订单状态" clearable style="width: 140px">
                    <el-option label="待付款" :value="1" />
                    <el-option label="待接单" :value="2" />
                    <el-option label="待服务" :value="3" />
                    <el-option label="服务中" :value="4" />
                    <el-option label="已完成" :value="5" />
                    <el-option label="已取消" :value="6" />
                    <el-option label="拒单" :value="7" />
                </el-select>
                <el-button type="primary" @click="load">查询</el-button>
            </div>

            <el-table :data="list" v-loading="loading" border>
                <el-table-column prop="orderNumber" label="订单号" width="200" />
                <el-table-column label="状态" width="90">
                    <template #default="{ row }">
                        <el-tag :type="statusTagType(row.status)">{{ statusText(row.status) }}</el-tag>
                    </template>
                </el-table-column>
                <el-table-column prop="consignee" label="联系人" width="90" />
                <el-table-column prop="phone" label="手机号" width="120" />
                <el-table-column prop="scheduleDate" label="上门日期" width="110" />
                <el-table-column prop="timeSlot" label="时段" width="120" />
                <el-table-column prop="address" label="地址" min-width="160" show-overflow-tooltip />
                <el-table-column prop="amount" label="金额" width="80" />
                <el-table-column label="操作" width="80" fixed="right">
                    <template #default="{ row }">
                        <el-button size="small" @click="openDetail(row)">详情</el-button>
                    </template>
                </el-table-column>
            </el-table>

            <el-pagination
                class="pager"
                layout="total, prev, pager, next"
                :total="total"
                :page-size="query.pageSize"
                :current-page="query.page"
                @current-change="onPageChange"
            />
        </el-card>

        <!-- 详情弹窗 -->
        <el-dialog v-model="detailVisible" title="订单详情" width="560px">
            <el-descriptions :column="1" border v-if="detail.id">
                <el-descriptions-item label="订单号">{{ detail.orderNumber }}</el-descriptions-item>
                <el-descriptions-item label="状态">{{ statusText(detail.status) }}</el-descriptions-item>
                <el-descriptions-item label="服务">{{ detail.orderDishes || '上门私教服务' }}</el-descriptions-item>
                <el-descriptions-item label="上门">{{ detail.scheduleDate }} {{ detail.timeSlot }}</el-descriptions-item>
                <el-descriptions-item label="地址">{{ detail.address }}</el-descriptions-item>
                <el-descriptions-item label="联系人">{{ detail.consignee }} {{ detail.phone }}</el-descriptions-item>
                <el-descriptions-item label="金额">¥{{ detail.amount }}</el-descriptions-item>
                <el-descriptions-item label="备注">{{ detail.remark || '无' }}</el-descriptions-item>
            </el-descriptions>
        </el-dialog>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import api from '../api.js';

const list = ref([]);
const total = ref(0);
const loading = ref(false);
const query = reactive({ page: 1, pageSize: 10, number: '', phone: '', status: null });

const detailVisible = ref(false);
const detail = ref({});

const statusMap = { 1: '待付款', 2: '待接单', 3: '待服务', 4: '服务中', 5: '已完成', 6: '已取消', 7: '拒单' };

function statusText(s) {
    return statusMap[s] || '未知';
}
function statusTagType(s) {
    return s === 5 ? 'success' : s === 1 ? 'warning' : s === 6 || s === 7 ? 'danger' : 'primary';
}

async function load() {
    loading.value = true;
    try {
        const data = await api.get('/admin/order/conditionSearch', {
            page: query.page,
            pageSize: query.pageSize,
            number: query.number,
            phone: query.phone,
            status: query.status
        });
        list.value = data.records || [];
        total.value = data.total || 0;
    } catch (e) {
        ElMessage.error(e.message);
    } finally {
        loading.value = false;
    }
}

function onPageChange(p) {
    query.page = p;
    load();
}

async function openDetail(row) {
    try {
        detail.value = await api.get('/admin/order/details/' + row.id);
        detailVisible.value = true;
    } catch (e) {
        ElMessage.error(e.message);
    }
}

onMounted(load);
</script>

<style scoped>
.toolbar {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
}
.pager {
    margin-top: 16px;
    justify-content: flex-end;
}
</style>
