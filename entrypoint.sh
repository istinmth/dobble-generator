#!/bin/bash
set -e

echo "Starting Dobble Generator container..."

# List all files and directories for debugging
echo "Contents of /app directory:"
ls -la /app

echo "Contents of templates directory:"
ls -la /app/templates || echo "Templates directory not found or empty"

echo "Contents of static directory:"
ls -la /app/static || echo "Static directory not found or empty"

# Create necessary directories with proper permissions
mkdir -p /app/uploads/icons /app/uploads/exports /app/logs
chmod -R 755 /app
chmod -R 777 /app/uploads /app/logs
chmod +x /app/*.py

# Check if templates exist
if [ ! -d "/app/templates" ] || [ -z "$(ls -A /app/templates 2>/dev/null)" ]; then
    echo "WARNING: Templates directory is missing or empty! Creating placeholder templates..."
    mkdir -p /app/templates

    # Create a basic template as fallback
    cat > /app/templates/base.html << 'EOL'
<!DOCTYPE html>
<html>
<head>
    <title>Dobble Generator</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #2c3e50; }
    </style>
</head>
<body>
    <h1>Dobble Generator</h1>
    <div>{% block content %}{% endblock %}</div>
</body>
</html>
EOL

    cat > /app/templates/index.html << 'EOL'
{% extends "base.html" %}
{% block content %}
<h2>Welcome to Dobble Generator</h2>
<p>This is a placeholder page. Please check the application files.</p>
{% endblock %}
EOL
fi

# Check if default icon sets directory exists
if [ ! -d "/app/static/default_icons" ]; then
    echo "Creating default icons directory..."
    mkdir -p /app/static/default_icons
fi

# Print debug info
echo "Environment variables:"
env

echo "Python packages:"
pip list

echo "Starting web application..."
# Start with gunicorn for production deployment
exec gunicorn --bind 0.0.0.0:8920 --workers 2 --threads 4 --timeout 120 --log-level debug --access-logfile - --error-logfile - app:app