<template>
    <div>
        <el-card>
            <div class="toolbar">
                <el-select v-model="statusFilter" placeholder="审核状态" clearable style="width: 160px" @change="load">
                    <el-option label="待审核" :value="0" />
                    <el-option label="正常" :value="1" />
                    <el-option label="已驳回" :value="2" />
                </el-select>
                <el-button type="primary" @click="load">查询</el-button>
            </div>

            <el-table :data="list" v-loading="loading" border>
                <el-table-column prop="id" label="ID" width="60" />
                <el-table-column prop="name" label="姓名" width="100" />
                <el-table-column prop="phone" label="手机号" width="130" />
                <el-table-column label="等级" width="90">
                    <template #default="{ row }">{{ levelText(row.level) }}</template>
                </el-table-column>
                <el-table-column prop="rating" label="评分" width="70" />
                <el-table-column prop="cityName" label="服务城市" width="100" />
                <el-table-column prop="bio" label="简介" show-overflow-tooltip />
                <el-table-column label="状态" width="90">
                    <template #default="{ row }">
                        <el-tag :type="statusTagType(row.status)">{{ statusText(row.status) }}</el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="120" fixed="right">
                    <template #default="{ row }">
                        <el-button v-if="row.status === 0" type="primary" size="small" @click="openAudit(row)">审核</el-button>
                        <el-button v-else type="warning" size="small" @click="openAudit(row)">重审</el-button>
                    </template>
                </el-table-column>
            </el-table>

            <el-pagination
                class="pager"
                layout="total, prev, pager, next"
                :total="total"
                :page-size="pageSize"
                :current-page="page"
                @current-change="onPageChange"
            />
        </el-card>

        <!-- 审核弹窗 -->
        <el-dialog v-model="auditVisible" title="教练审核" width="640px" @open="loadDetail">
            <p>教练：<b>{{ current.name }}</b>（{{ current.phone }}）</p>
            <div v-if="detail.bio" style="margin: 8px 0; color: #606266;">简介：{{ detail.bio }}</div>

            <!-- 资质证书列表 -->
            <div v-if="detail.certificates && detail.certificates.length" style="margin: 12px 0;">
                <h4 style="margin: 8px 0;">资质证书</h4>
                <el-table :data="detail.certificates" border size="small">
                    <el-table-column prop="certType" label="证书类型" width="120" />
                    <el-table-column prop="certNo" label="证书编号" width="160" />
                    <el-table-column label="状态" width="80">
                        <template #default="{ row }">
                            <el-tag :type="certStatusType(row.status)" size="small">{{ certStatusText(row.status) }}</el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column label="证书图片" width="100">
                        <template #default="{ row }">
                            <el-image
                                v-if="row.imageUrl"
                                :src="row.imageUrl"
                                :preview-src-list="[row.imageUrl]"
                                fit="cover"
                                style="width: 60px; height: 40px; cursor: pointer;"
                            />
                            <span v-else>无</span>
                        </template>
                    </el-table-column>
                    <el-table-column prop="rejectReason" label="驳回原因" show-overflow-tooltip />
                </el-table>
            </div>

            <el-divider />

            <el-radio-group v-model="auditForm.status">
                <el-radio :label="1">通过</el-radio>
                <el-radio :label="2">驳回</el-radio>
            </el-radio-group>
            <el-input
                v-if="auditForm.status === 2"
                v-model="auditForm.rejectReason"
                type="textarea"
                placeholder="驳回原因"
                style="margin-top: 16px"
            />
            <template #footer>
                <el-button @click="auditVisible = false">取消</el-button>
                <el-button type="primary" @click="submitAudit">确定</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import api from '../api.js';

const list = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(10);
const statusFilter = ref(null);
const loading = ref(false);

const auditVisible = ref(false);
const current = ref({});
const auditForm = ref({ status: 1, rejectReason: '' });
const detail = ref({});

const levelMap = { 1: '初级', 2: '中级', 3: '高级', 4: '金牌' };
const statusMap = { 0: '待审核', 1: '正常', 2: '已驳回' };
const certStatusMap = { 0: '待审核', 1: '已通过', 2: '已驳回' };

function levelText(l) {
    return levelMap[l] || '未知';
}
function statusText(s) {
    return statusMap[s] || '未知';
}
function statusTagType(s) {
    return s === 0 ? 'warning' : s === 1 ? 'success' : 'danger';
}
function certStatusText(s) {
    return certStatusMap[s] || '未知';
}
function certStatusType(s) {
    return s === 0 ? 'warning' : s === 1 ? 'success' : 'danger';
}

async function load() {
    loading.value = true;
    try {
        const data = await api.get('/admin/coach/page', {
            page: page.value,
            pageSize: pageSize.value,
            status: statusFilter.value
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
    page.value = p;
    load();
}

function openAudit(row) {
    current.value = row;
    auditForm.value = { status: 1, rejectReason: '' };
    detail.value = {};
    auditVisible.value = true;
}

async function loadDetail() {
    if (!current.value.id) return;
    try {
        detail.value = await api.get('/admin/coach/' + current.value.id);
    } catch (e) {
        ElMessage.error('加载教练详情失败：' + e.message);
    }
}

async function submitAudit() {
    try {
        await api.post('/admin/coach/audit', {
            coachId: current.value.id,
            status: auditForm.value.status,
            rejectReason: auditForm.value.status === 2 ? auditForm.value.rejectReason : null
        });
        ElMessage.success('审核完成');
        auditVisible.value = false;
        load();
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
