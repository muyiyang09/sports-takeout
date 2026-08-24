# 体育外卖后端 Dockerfile (多阶段构建)
FROM maven:3.8-openjdk-8 AS builder
WORKDIR /build
COPY pom.xml .
COPY sky-common/pom.xml sky-common/
COPY sky-pojo/pom.xml sky-pojo/
COPY sky-server/pom.xml sky-server/
RUN mvn dependency:go-offline -B
COPY . .
RUN mvn clean package -DskipTests -q

FROM openjdk:8-jre-slim
WORKDIR /app
COPY --from=builder /build/sky-server/target/sky-server-*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar", "--spring.profiles.active=docker"]
