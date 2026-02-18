#!/bin/sh

# Extract DNS resolver from container's /etc/resolv.conf
# This avoids hardcoding Docker's DNS IP and makes it portable
DNS_RESOLVER=$(awk '/^nameserver/{print $2; exit}' /etc/resolv.conf)

if [ -z "$DNS_RESOLVER" ]; then
    echo "Error: Could not detect DNS resolver from /etc/resolv.conf"
    echo "Please ensure the container has proper DNS configuration"
    exit 1
fi

export DNS_RESOLVER

# Substitute environment variables in nginx config
envsubst '\${BACKEND_URL}\${DNS_RESOLVER}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx (runs as root but worker processes drop to nginx user)
exec nginx -g 'daemon off;'
