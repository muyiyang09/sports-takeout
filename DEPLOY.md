# 体育外卖 · 上门私教平台 — 部署指南

## 一、Docker Compose 一键部署（推荐）

### 前置条件
- 已安装 Docker 和 Docker Compose

### 步骤

```bash
# 1. 克隆仓库
git clone https://github.com/yourname/sports-takeout.git
cd sports-takeout

# 2. 复制环境变量文件并修改
cp .env.example .env
# 编辑 .env，至少修改 MYSQL_ROOT_PASSWORD

# 3. 一键启动（首次会自动构建镜像 + 初始化数据库）
docker-compose up -d

# 4. 查看启动状态
docker-compose ps

# 5. 查看后端日志
docker-compose logs -f backend
```

### 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 后端 API | http://localhost:8080 | Spring Boot + Knife4j |
| 接口文档 | http://localhost:8080/doc.html | Knife4j UI |
| 管理端前端 | http://localhost:5173 | Vue3 + Element Plus |
| MySQL | localhost:3306 | 用户 root / 密码见 .env |
| Redis | localhost:6379 | 无密码 |

### 默认管理员账号
- 用户名：admin
- 密码：123456

### 停止 / 清理

```bash
# 停止
docker-compose down

# 停止并删除数据卷（清空数据库）
docker-compose down -v
```

---

## 二、本地开发部署（不用 Docker）

### 前置条件
- JDK 21
- Maven 3.6+
- MySQL 8.0
- Redis 7+
- Node.js 18+

### 后端启动

```bash
# 1. 创建数据库并导入表结构
mysql -u root -p < sql/sports_take_out.sql

# 2. 修改配置
# 编辑 sky-take-out/sky-server/src/main/resources/application-dev.yml
# 修改数据库密码、Redis 地址等

# 3. 编译并启动
cd sky-take-out
mvn clean package -DskipTests -q
java -jar sky-server/target/sky-server-*.jar
```

### 管理端前端启动

```bash
cd admin-web
npm install
npm run dev
# 访问 http://localhost:5173
```

### 小程序启动

1. 打开微信开发者工具
2. 导入 `uniapp-user` 目录（用户端）或 `uniapp-coach` 目录（教练端）
3. 修改 `utils/request.js` 中的 `baseUrl` 为你的后端地址

---

## 三、目录结构

```
sports-takeout/
├── docker-compose.yml          # Docker Compose 编排
├── .env.example                # 环境变量模板
├── DEPLOY.md                   # 本文档
├── sql/sports_take_out.sql     # 数据库建表 + 种子数据（14 张表）
├── sky-take-out/               # 后端工程
│   ├── Dockerfile              # 后端容器构建
│   ├── sky-common/             # 公共模块（工具类/常量/异常）
│   ├── sky-pojo/               # 实体/DTO/VO
│   └── sky-server/             # Spring Boot 主工程
│       └── src/main/resources/
│           ├── application.yml         # 主配置
│           ├── application-dev.yml     # 开发环境配置
│           └── application-docker.yml  # Docker 环境配置
├── admin-web/                  # 管理端 PC 前端
│   ├── Dockerfile              # 前端容器构建
│   ├── nginx.conf              # Nginx 反向代理配置
│   └── src/views/
│       ├── LoginView.vue       # 登录页
│       ├── CoachView.vue       # 教练审核（含资质证书预览）
│       ├── CourseView.vue      # 课程管理（CRUD + 上下架）
│       ├── OrderView.vue       # 订单管理（搜索 + 详情）
│       └── DispatchPoolView.vue # 派单池监控
├── uniapp-user/                # 用户端小程序
└── uniapp-coach/               # 教练端小程序
```

---

## 四、常见问题

### Q: 启动后接口返回 500？
A: 检查 MySQL 和 Redis 是否正常启动。后端日志会打印连接异常。

### Q: 管理端登录提示 401？
A: 确认后端已启动，且 `application-dev.yml` 中的数据库配置正确。默认账号 admin/123456。

### Q: 小程序请求被拒绝（ERR_CONNECTION_REFUSED）？
A: 检查后端是否在 8080 端口运行，且小程序的 `baseUrl` 配置正确。

### Q: 图片上传不成功？
A: 需要配置阿里云 OSS。在 `.env` 中填写 `SKY_OSS_AK` 和 `SKY_OSS_SK`。
