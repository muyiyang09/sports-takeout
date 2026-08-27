# ai-service 生产镜像（#05 商业化加固）
# 多阶段没必要（纯 Python 服务，无编译产物），用单阶段 + 非 root + 健康探针。
FROM python:3.11-slim

WORKDIR /app

# 复制源码 + 依赖清单，装包（含全部依赖）
COPY . .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# 非 root 运行（安全合规硬指标）
RUN useradd -m -u 1000 appuser
USER appuser

# 关闭字节码缓存 + 强制无缓冲输出（日志实时进采集器）
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 18000

# 用 Python 内置 urllib 做健康检查（slim 镜像无 curl，避免额外 apt 安装）
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:18000/healthz', timeout=3)"

# --workers 2：每进程独立连接池(BM25索引/MySQL池/Redis池)，2 副本平衡吞吐与 MySQL 连接数
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "18000", "--workers", "2", "--timeout-graceful-shutdown", "30"]
