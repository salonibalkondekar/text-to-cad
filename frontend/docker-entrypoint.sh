#!/bin/sh

# Substitute environment variables in HTML files
echo "Substituting API_URL=${API_URL} in HTML files..."

# Replace placeholder in index.html
envsubst '${API_URL}' < /usr/share/nginx/html/index.html > /tmp/index.html
mv /tmp/index.html /usr/share/nginx/html/index.html

echo "Environment variable substitution completed."

# Execute the original command
exec "$@"
