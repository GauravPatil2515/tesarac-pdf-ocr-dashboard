# Deployment Guide

This guide covers different deployment options for the Medical PDF OCR Dashboard.

## Table of Contents
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Configuration](#configuration)
- [Security Considerations](#security-considerations)

## Local Development

For development and testing:

```bash
# Clone the repository
git clone https://github.com/yourusername/tesarac.git
cd tesarac

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python start.py
```

The application will be available at `http://localhost:5000`.

## Production Deployment

### Using Gunicorn (Recommended)

1. Install Gunicorn:
```bash
pip install gunicorn
```

2. Create a Gunicorn configuration file (`gunicorn.conf.py`):
```python
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

3. Run with Gunicorn:
```bash
gunicorn -c gunicorn.conf.py app:app
```

### Using uWSGI

1. Install uWSGI:
```bash
pip install uwsgi
```

2. Create uWSGI configuration (`uwsgi.ini`):
```ini
[uwsgi]
module = app:app
master = true
processes = 4
socket = /tmp/tesarac.sock
chmod-socket = 666
vacuum = true
die-on-term = true
```

3. Run with uWSGI:
```bash
uwsgi --ini uwsgi.ini
```

### Nginx Configuration

For production, use Nginx as a reverse proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    client_max_body_size 200M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /path/to/tesarac/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Docker Deployment

### Dockerfile

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads outputs

# Expose port
EXPOSE 5000

# Run the application
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
```

### Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  tesarac:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
    environment:
      - FLASK_ENV=production
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - tesarac
    restart: unless-stopped
```

Build and run:
```bash
docker-compose up -d
```

## Cloud Deployment

### AWS EC2

1. Launch an EC2 instance (Ubuntu 20.04 LTS recommended)
2. Install dependencies:
```bash
sudo apt update
sudo apt install python3-pip python3-venv tesseract-ocr nginx
```

3. Clone and setup the application:
```bash
git clone https://github.com/yourusername/tesarac.git
cd tesarac
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

4. Configure systemd service (`/etc/systemd/system/tesarac.service`):
```ini
[Unit]
Description=Tesarac PDF OCR Dashboard
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/tesarac
Environment=PATH=/home/ubuntu/tesarac/.venv/bin
ExecStart=/home/ubuntu/tesarac/.venv/bin/gunicorn -c gunicorn.conf.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

5. Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable tesarac
sudo systemctl start tesarac
```

### Heroku

1. Create a `Procfile`:
```
web: gunicorn app:app
```

2. Create `runtime.txt`:
```
python-3.9.18
```

3. Add Heroku buildpacks:
```bash
heroku buildpacks:add heroku/python
heroku buildpacks:add https://github.com/heroku/heroku-buildpack-apt
```

4. Create `Aptfile`:
```
tesseract-ocr
tesseract-ocr-eng
poppler-utils
```

5. Deploy:
```bash
git push heroku main
```

## Configuration

### Environment Variables

Set these environment variables for production:

```bash
export FLASK_ENV=production
export FLASK_SECRET_KEY=your-secret-key-here
export MAX_CONTENT_LENGTH=209715200  # 200MB
export UPLOAD_FOLDER=/app/uploads
export OUTPUT_FOLDER=/app/outputs
```

### Security Settings

- Use HTTPS in production
- Set secure session cookies
- Implement rate limiting
- Configure proper file permissions
- Use environment variables for sensitive data

## Security Considerations

1. **File Upload Security**:
   - Validate file types and extensions
   - Limit file sizes
   - Scan for malware
   - Use secure file storage

2. **Network Security**:
   - Use HTTPS/TLS
   - Implement rate limiting
   - Configure firewall rules
   - Monitor access logs

3. **Application Security**:
   - Keep dependencies updated
   - Use secure session management
   - Implement proper error handling
   - Log security events

4. **Infrastructure Security**:
   - Regular security updates
   - Backup strategies
   - Access control
   - Network segmentation

## Monitoring and Logging

- Monitor application performance
- Set up log rotation
- Track error rates
- Monitor resource usage
- Set up alerts for failures

## Backup and Recovery

- Regular database backups (if applicable)
- File system backups
- Configuration backups
- Disaster recovery plan
- Testing recovery procedures
