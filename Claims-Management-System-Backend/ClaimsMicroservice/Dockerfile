# Multi-stage Dockerfile for Claims Microservice
# Build stage: Use Maven to compile and package the application
FROM openjdk:17-jdk-slim AS build

# Set working directory
WORKDIR /app

# Copy Maven configuration files
COPY pom.xml .
COPY .mvn/wrapper/maven-wrapper.properties /app/.mvn/wrapper/

# Download dependencies in separate layer for caching
RUN mvn dependency:go-offline -B

# Copy application source code
COPY src ./src

# Build the application (skip tests for faster builds)
RUN mvn clean package -DskipTests

# Runtime stage: Use slim JRE image for production
FROM openjdk:17-jre-slim

# Create non-root user for security
RUN useradd -ms /bin/bash appuser && mkdir -p /app
USER appuser
WORKDIR /app

# Copy the built JAR file from the build stage
COPY --from=build /app/target/ClaimsMicroservice-*.jar app.jar

# Expose the application port
EXPOSE 8090

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8090/claims/actuator/health || exit 1

# Set entrypoint to run the Spring Boot application
ENTRYPOINT ["java", "-jar", "app.jar"]