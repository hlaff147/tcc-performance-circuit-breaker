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

# Instala curl para health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY --from=builder /workspace/target/servico-pagamento-v2-2.0.0.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
