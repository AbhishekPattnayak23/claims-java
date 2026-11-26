# Multi-stage Dockerfile for Angular Frontend
# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy source code and build
COPY . .
RUN npm run build -- --configuration production

# Runtime stage
FROM nginx:alpine

# Remove default nginx static files
RUN rm -rf /usr/share/nginx/html/*

# Copy built artifacts from build stage
COPY --from=build /app/dist/claims-management-system-frontend /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

# Run as non-root user
RUN addgroup -g 1001 -S nginxgroup && \
    adduser -S nginxuser -G nginxgroup -u 1001 && \
    chown -R nginxuser:nginxgroup /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

USER nginxuser

# Start nginx
CMD ["nginx", "-g", "daemon off;"]