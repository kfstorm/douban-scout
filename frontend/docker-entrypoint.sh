#!/bin/sh

# Substitute environment variables in nginx config
envsubst '\${BACKEND_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx (runs as root but worker processes drop to nginx user)
exec nginx -g 'daemon off;'
