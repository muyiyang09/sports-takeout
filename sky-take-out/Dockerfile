# 体育外卖后端 Dockerfile (多阶段构建，JDK 21 对齐 Boot 3.5)
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /build
COPY pom.xml .
COPY sky-common/pom.xml sky-common/
COPY sky-pojo/pom.xml sky-pojo/
COPY sky-server/pom.xml sky-server/
RUN mvn dependency:go-offline -B
COPY . .
RUN mvn clean package -DskipTests -q

FROM eclipse-temurin:21-jre
# 非 root 运行 + 装 curl 供健康探针用（temurin 基础镜像无 curl）
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r app && useradd -r -g app appuser
WORKDIR /app
COPY --from=builder /build/sky-server/target/sky-server-*.jar app.jar
USER appuser
EXPOSE 8080
# 健康探针：依赖 /actuator/health（见 spring-boot-starter-actuator）
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=90s \
    CMD curl -fsS http://localhost:8080/actuator/health || exit 1
ENTRYPOINT ["java", "-jar", "app.jar", "--spring.profiles.active=docker"]
