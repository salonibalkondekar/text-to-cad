# Frontend Dockerfile
FROM nginx:alpine
WORKDIR /usr/share/nginx/html
COPY . .
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Set default API_URL if not provided
ENV API_URL=http://localhost:8000

# Substitute environment variables in HTML files at runtime
RUN apk add --no-cache gettext
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
