# Legal Case Management System - Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Application Deployment](#application-deployment)
4. [Database Migration](#database-migration)
5. [Security Configuration](#security-configuration)
6. [Performance Optimization](#performance-optimization)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- Ubuntu 20.04 LTS or later
- Python 3.9+
- PostgreSQL 13+ (for production)
- Nginx
- Gunicorn
- Supervisor

### Required Software
```bash
sudo apt update
sudo apt install python3.9 python3.9-venv python3.9-dev
sudo apt install postgresql postgresql-contrib
sudo apt install nginx
sudo apt install supervisor
```

## Server Setup

### 1. Create Application User
```bash
sudo adduser legal_app
sudo usermod -aG sudo legal_app
```

### 2. Directory Structure
```bash
sudo mkdir -p /opt/legal_case_management
sudo chown legal_app:legal_app /opt/legal_case_management
cd /opt/legal_case_management
```

### 3. Clone Repository
```bash
git clone https://github.com/your-org/legal_case_management.git .
```

### 4. Create Virtual Environment
```bash
python3.9 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Application Deployment

### 1. Environment Configuration
Create a `.env` file with production settings:
```bash
# Django Settings
DJANGO_SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_ENV=production

# Database
DB_NAME=legal_case_db
DB_USER=legal_db_user
DB_PASSWORD=secure-password
DB_HOST=localhost
DB_PORT=5432

# Security
DOCUMENT_ENCRYPTION_KEY=your-encryption-key
ADMIN_IP_WHITELIST=123.123.123.123,124.124.124.124

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# AI Services
ENABLE_AI_FEATURES=True
DEFAULT_LLM_ENDPOINT=http://127.0.0.1:1234/v1/chat/completions
```

### 2. Generate Encryption Key
```bash
python manage.py generate_encryption_key --save encryption.key
# Store the key securely and add to .env
```

### 3. Static Files
```bash
python manage.py collectstatic --noinput
```

### 4. Gunicorn Configuration
Create `/opt/legal_case_management/gunicorn_config.py`:
```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "/var/log/legal_app/gunicorn_access.log"
errorlog = "/var/log/legal_app/gunicorn_error.log"
loglevel = "info"
```

### 5. Supervisor Configuration
Create `/etc/supervisor/conf.d/legal_app.conf`:
```ini
[program:legal_app]
command=/opt/legal_case_management/venv/bin/gunicorn legal_case_management.wsgi:application -c /opt/legal_case_management/gunicorn_config.py
directory=/opt/legal_case_management
user=legal_app
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/legal_app/supervisor.log
environment=PATH="/opt/legal_case_management/venv/bin"
```

### 6. Nginx Configuration
Create `/etc/nginx/sites-available/legal_app`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/your_certificate.crt;
    ssl_certificate_key /etc/ssl/private/your_private.key;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /opt/legal_case_management/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
    
    location /media/ {
        alias /opt/legal_case_management/media/;
        expires 7d;
        add_header Cache-Control "public, no-transform";
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/legal_app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Database Migration

### 1. PostgreSQL Setup
```sql
sudo -u postgres psql
CREATE DATABASE legal_case_db;
CREATE USER legal_db_user WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE legal_case_db TO legal_db_user;
\q
```

### 2. Migrate from SQLite to PostgreSQL
```bash
# Backup SQLite data
python manage.py dumpdata > data_backup.json

# Update settings to use PostgreSQL
export DJANGO_SETTINGS_MODULE=legal_case_management.settings.production

# Run migrations
python manage.py migrate

# Load data into PostgreSQL
python manage.py loaddata data_backup.json
```

## Security Configuration

### 1. Check Security Settings
```bash
python manage.py check_security
```

### 2. SSL/TLS Configuration
- Use Let's Encrypt for free SSL certificates:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 3. Firewall Configuration
```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

### 4. Regular Security Updates
```bash
# Create update script
cat > /opt/legal_case_management/update_security.sh << 'EOF'
#!/bin/bash
source /opt/legal_case_management/venv/bin/activate
pip install --upgrade pip
pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip install -U
python manage.py check_security
EOF

chmod +x /opt/legal_case_management/update_security.sh
```

## Performance Optimization

### 1. Database Optimization
```sql
-- Create indexes for frequently queried fields
CREATE INDEX idx_case_status ON cases_case(status);
CREATE INDEX idx_case_client ON cases_case(client_id);
CREATE INDEX idx_document_case ON documents_document(case_id);
```

### 2. Redis Cache Setup
```bash
sudo apt install redis-server
sudo systemctl enable redis-server
```

Update cache settings in production:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### 3. Enable Compression
```bash
# Already configured in Nginx, but ensure gzip is enabled
sudo nano /etc/nginx/nginx.conf
# Add/verify:
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
```

## Monitoring and Maintenance

### 1. Log Rotation
Create `/etc/logrotate.d/legal_app`:
```
/var/log/legal_app/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 legal_app legal_app
    sharedscripts
    postrotate
        systemctl reload supervisor
    endscript
}
```

### 2. Database Backup
Create backup script `/opt/legal_case_management/backup_db.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/opt/legal_case_management/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="legal_case_db"

mkdir -p $BACKUP_DIR
pg_dump -U legal_db_user -h localhost $DB_NAME > $BACKUP_DIR/db_backup_$TIMESTAMP.sql
gzip $BACKUP_DIR/db_backup_$TIMESTAMP.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /opt/legal_case_management/backup_db.sh
```

### 3. Monitoring Tools
```bash
# Install monitoring tools
sudo apt install htop iotop

# Monitor application logs
tail -f /var/log/legal_app/supervisor.log
tail -f /var/log/legal_app/gunicorn_access.log
tail -f /var/log/nginx/access.log
```

### 4. Regular Maintenance Tasks
```bash
# Clean up old data
python manage.py cleanup_old_data --days 365 --all

# Vacuum PostgreSQL database
sudo -u postgres psql -d legal_case_db -c "VACUUM ANALYZE;"
```

## Troubleshooting

### Common Issues

1. **Application Won't Start**
   - Check supervisor logs: `tail -f /var/log/legal_app/supervisor.log`
   - Verify gunicorn configuration
   - Check permissions on directories

2. **Database Connection Issues**
   - Verify PostgreSQL is running: `sudo systemctl status postgresql`
   - Check database credentials in .env
   - Test connection: `psql -h localhost -U legal_db_user -d legal_case_db`

3. **Static Files Not Loading**
   - Run `python manage.py collectstatic`
   - Check Nginx configuration
   - Verify file permissions

4. **High Memory Usage**
   - Adjust gunicorn workers
   - Check for memory leaks in custom code
   - Monitor with: `htop`

5. **Slow Performance**
   - Enable query debugging in development
   - Check database indexes
   - Review slow query logs

### Useful Commands

```bash
# Restart application
sudo supervisorctl restart legal_app

# Check application status
sudo supervisorctl status legal_app

# Restart Nginx
sudo systemctl restart nginx

# View recent errors
tail -n 100 /var/log/legal_app/gunicorn_error.log

# Django shell access
source /opt/legal_case_management/venv/bin/activate
python manage.py shell

# Database shell access
python manage.py dbshell
```

## Support and Maintenance

For support:
1. Check logs for errors
2. Review this documentation
3. Contact the development team at: support@example.com

Regular maintenance checklist:
- [ ] Daily: Check logs for errors
- [ ] Weekly: Review security updates
- [ ] Monthly: Database optimization
- [ ] Quarterly: Security audit
- [ ] Yearly: Major version upgrades
