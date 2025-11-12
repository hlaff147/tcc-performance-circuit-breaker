# syntax=docker/dockerfile:1

FROM maven:3.8.7-eclipse-temurin-17 AS builder
WORKDIR /workspace

# Cache Maven dependencies
COPY pom.xml ./
RUN mvn dependency:go-offline -B || true

# Build application with retry
COPY src ./src
RUN mvn -B package -DskipTests -Dmaven.wagon.http.retryHandler.count=3 -Dmaven.wagon.httpconnectionManager.ttlSeconds=120

FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=builder /workspace/target/servico-pagamento-v1-0.0.1-SNAPSHOT.jar app.jar
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
