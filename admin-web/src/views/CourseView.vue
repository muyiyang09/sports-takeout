<template>
    <div>
        <el-card>
            <div class="toolbar">
                <el-button type="primary" @click="openAdd">新增课程</el-button>
            </div>

            <el-table :data="list" v-loading="loading" border>
                <el-table-column prop="id" label="ID" width="60" />
                <el-table-column prop="name" label="课程名称" min-width="140" />
                <el-table-column prop="categoryName" label="分类" width="100" />
                <el-table-column prop="price" label="价格" width="80" />
                <el-table-column prop="intensity" label="强度" width="70" />
                <el-table-column prop="durationMin" label="时长(分)" width="90" />
                <el-table-column prop="suitCrowd" label="适合人群" min-width="140" show-overflow-tooltip />
                <el-table-column label="状态" width="80">
                    <template #default="{ row }">
                        <el-tag :type="row.status === 1 ? 'success' : 'info'">{{ row.status === 1 ? '起售' : '停售' }}</el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="180" fixed="right">
                    <template #default="{ row }">
                        <el-button size="small" @click="openEdit(row)">编辑</el-button>
                        <el-button size="small" :type="row.status === 1 ? 'warning' : 'success'" @click="toggleStatus(row)">
                            {{ row.status === 1 ? '停售' : '起售' }}
                        </el-button>
                        <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
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

        <!-- 新增/编辑弹窗 -->
        <el-dialog v-model="formVisible" :title="form.id ? '编辑课程' : '新增课程'" width="520px">
            <el-form label-width="90px">
                <el-form-item label="课程名称">
                    <el-input v-model="form.name" />
                </el-form-item>
                <el-form-item label="分类">
                    <el-select v-model="form.categoryId" placeholder="选择分类" style="width: 100%">
                        <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
                    </el-select>
                </el-form-item>
                <el-form-item label="价格">
                    <el-input-number v-model="form.price" :min="0" :precision="2" style="width: 100%" />
                </el-form-item>
                <el-form-item label="强度">
                    <el-select v-model="form.intensity" style="width: 100%">
                        <el-option label="轻" value="轻" />
                        <el-option label="中" value="中" />
                        <el-option label="高" value="高" />
                    </el-select>
                </el-form-item>
                <el-form-item label="时长(分钟)">
                    <el-input-number v-model="form.durationMin" :min="1" style="width: 100%" />
                </el-form-item>
                <el-form-item label="适合人群">
                    <el-input v-model="form.suitCrowd" />
                </el-form-item>
                <el-form-item label="所需器械">
                    <el-input v-model="form.equipment" placeholder="逗号分隔，如 弹力带,壶铃" />
                </el-form-item>
                <el-form-item label="课程描述">
                    <el-input v-model="form.description" type="textarea" />
                </el-form-item>
                <el-form-item label="状态">
                    <el-switch v-model="form.status" :active-value="1" :inactive-value="0" active-text="起售" inactive-text="停售" />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="formVisible = false">取消</el-button>
                <el-button type="primary" @click="save">保存</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../api';

const list = ref([]);
const categories = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(10);
const loading = ref(false);
const formVisible = ref(false);
const form = ref({});

function emptyForm() {
    return { name: '', categoryId: null, price: 0, intensity: '中', durationMin: 60, suitCrowd: '', equipment: '', description: '', status: 1 };
}

async function loadCategories() {
    try {
        categories.value = (await api.get('/admin/category/list', { type: 1 })) || [];
    } catch (e) {}
}

async function load() {
    loading.value = true;
    try {
        const data = await api.get('/admin/course/page', { page: page.value, pageSize: pageSize.value });
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

function openAdd() {
    form.value = emptyForm();
    formVisible.value = true;
}

function openEdit(row) {
    form.value = { ...row };
    formVisible.value = true;
}

async function save() {
    try {
        if (form.value.id) {
            await api.put('/admin/course', form.value);
        } else {
            await api.post('/admin/course', form.value);
        }
        ElMessage.success('保存成功');
        formVisible.value = false;
        load();
    } catch (e) {
        ElMessage.error(e.message);
    }
}

async function toggleStatus(row) {
    const target = row.status === 1 ? 0 : 1;
    try {
        await api.post('/admin/course/status/' + target + '?id=' + row.id);
        ElMessage.success('已更新');
        load();
    } catch (e) {
        ElMessage.error(e.message);
    }
}

async function remove(row) {
    try {
        await ElMessageBox.confirm('确认删除课程「' + row.name + '」？', '提示', { type: 'warning' });
        await api.del('/admin/course?ids=' + row.id);
        ElMessage.success('已删除');
        load();
    } catch (e) {
        if (e !== 'cancel') ElMessage.error(e.message);
    }
}

onMounted(() => {
    load();
    loadCategories();
});
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
