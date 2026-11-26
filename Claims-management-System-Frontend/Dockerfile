# Multi-stage Dockerfile for Angular application
# Build stage: Node.js for Angular build
FROM node:20-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build Angular application for production
RUN npm run build -- --configuration production

# Production stage: Nginx to serve static files
FROM nginx:alpine AS production

# Install bash for debugging (optional, can be removed)
RUN apk add --no-cache bash

# Remove default nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/

# Copy built application from build stage
COPY --from=build /app/dist/claims-management-system-frontend /usr/share/nginx/html

# Create non-root user
RUN addgroup -g 1001 -S nginxgroup && \
    adduser -S nginxuser -u 1001 -G nginxgroup

# Change ownership of nginx directories
RUN chown -R nginxuser:nginxgroup /var/cache/nginx && \
    chown -R nginxuser:nginxgroup /var/run && \
    chown -R nginxuser:nginxgroup /usr/share/nginx/html && \
    chown -R nginxuser:nginxgroup /etc/nginx/conf.d

# Switch to non-root user
USER nginxuser

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]