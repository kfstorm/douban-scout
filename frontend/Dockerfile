# Build stage
FROM node:20-bookworm AS builder

WORKDIR /app

# Copy package files first for better layer caching
COPY package*.json ./

# Install dependencies with cache mount
RUN --mount=type=cache,target=/tmp/npm-cache \
    npm ci --cache /tmp/npm-cache

# Copy only files needed for the build
COPY index.html ./
COPY vite.config.ts ./
COPY tsconfig*.json ./
COPY postcss.config.js ./
COPY src ./src
COPY public ./public

# Build (cached unless source files change)
RUN npm run build

# Runtime stage
FROM nginx:alpine

# Install gettext for envsubst
RUN apk add --no-cache gettext

# Copy built static files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration template
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Set default backend URL (can be overridden at runtime)
ENV BACKEND_URL=http://localhost:8000

# Expose port
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8080/ || exit 1

# Use entrypoint script (runs as root to write config, then drops to nginx)
ENTRYPOINT ["/docker-entrypoint.sh"]
