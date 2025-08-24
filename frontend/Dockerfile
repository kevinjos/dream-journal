# Multi-stage build for Quasar frontend
FROM node:22-slim as builder

# Set working directory
WORKDIR /app

# Copy package files and essential Quasar configuration
COPY package*.json ./
COPY quasar.config.ts ./
COPY tsconfig.json ./
COPY eslint.config.js ./
COPY postcss.config.js ./
COPY index.html ./
COPY public/ ./public/

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the SPA
RUN npm run build

# Production stage using unprivileged nginx
FROM nginxinc/nginx-unprivileged:alpine

# Copy built SPA from builder
COPY --from=builder /app/dist/spa /usr/share/nginx/html

# Copy nginx configuration
COPY --chown=nginx:nginx nginx.conf /etc/nginx/nginx.conf

# Expose port (unprivileged nginx uses 8080)
EXPOSE 8080

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
