# Decian Custom IRIS Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the Decian customized IRIS platform in production environments.

## 🎯 What You're Getting
- **Base IRIS v2.4.22** with all standard features
- **Threat Intelligence Integration** with MISP
- **Enhanced Branding** (Ironclad Case Management)
- **SOAR Integrations** (SentinelOne, Velociraptor)
- **Enhanced Documentation** and playbooks

## 🚀 Quick Start (Recommended)

### 1. Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM and 20GB disk space
- Access to MISP instance at `https://misp.ironclad.decianx`
- Valid MISP API key

### 2. Download and Setup
```bash
# Clone or extract the project
git clone <repository-url> decian-iris
cd decian-iris

# Copy environment template
cp .env.template .env

# Edit configuration (see Configuration section below)
nano .env
```

### 3. Deploy
```bash
# Start production deployment
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

### 4. Initial Access
- URL: `https://localhost:443` (or your configured port)
- Default credentials will be created based on your `.env` file
- Navigate to **Threat Intel** tab to test MISP integration

## 📋 Configuration

### Required Environment Variables
Edit `.env` file with your specific values:

```bash
# Database (Change these!)
POSTGRES_PASSWORD=your_secure_postgres_password_here
IRIS_SECRET_KEY=your_very_long_random_secret_key_here_minimum_32_characters
IRIS_SECURITY_PASSWORD_SALT=your_secure_password_salt_here

# Admin Account
ADMIN_EMAIL=admin@yourcompany.com
ADMIN_USERNAME=administrator
ADMIN_PASSWORD=your_secure_admin_password_here

# MISP Integration (Critical for Threat Intel)
MISP_URL=https://misp.ironclad.decianx
MISP_API_KEY=your_misp_api_key_here

# Optional Customization
ORGANIZATION_NAME=Your Company Name
HTTPS_PORT=443
```

### Generating Secure Keys
```bash
# Generate secret key (Linux/Mac)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate password salt
python3 -c "import secrets; print(secrets.token_urlsafe(16))"

# Generate secure password
openssl rand -base64 32
```

## 🐳 Docker Image Distribution

### Option 1: Use Pre-built Images (Recommended)
If images are available in a registry:
```bash
docker pull decian/iris-app:v2.4.22-custom
docker pull decian/iris-db:v2.4.22-custom
docker pull decian/iris-nginx:v2.4.22-custom
```

### Option 2: Build Images Locally
```bash
# Make build script executable
chmod +x build-images.sh

# Build all custom images
./build-images.sh
```

### Option 3: Import from Saved Files
If you received tar.gz image files:
```bash
docker load < iris-app-custom.tar.gz
docker load < iris-db-custom.tar.gz
docker load < iris-nginx-custom.tar.gz
```

## 🔧 Advanced Configuration

### Custom SSL Certificates
1. Place your certificates in `certificates/web_certificates/`
2. Update docker-compose volume mapping if needed
3. Restart nginx container

### MISP Integration Verification
```bash
# Test MISP connectivity
curl -k -H "Authorization: YOUR_API_KEY" https://misp.ironclad.decianx/events/index

# Check IRIS logs for MISP errors
docker-compose -f docker-compose.production.yml logs app | grep -i misp
```

### Database Persistence
Production volumes are automatically created:
- `db_data`: PostgreSQL data
- `app_data`: IRIS application data
- `nginx_certs`: SSL certificates
- `nginx_logs`: Nginx access/error logs

## 🛠️ Maintenance

### Backups
```bash
# Database backup
docker-compose -f docker-compose.production.yml exec db pg_dump -U postgres iris_db > backup_$(date +%Y%m%d).sql

# Application data backup
docker run --rm -v decian-iris_app_data:/volume -v $(pwd):/backup alpine tar czf /backup/app_data_$(date +%Y%m%d).tar.gz -C /volume .
```

### Updates
```bash
# Stop services
docker-compose -f docker-compose.production.yml down

# Pull new images (if using registry)
docker-compose -f docker-compose.production.yml pull

# Start services
docker-compose -f docker-compose.production.yml up -d
```

### Monitoring
```bash
# View all service status
docker-compose -f docker-compose.production.yml ps

# Monitor logs in real-time
docker-compose -f docker-compose.production.yml logs -f

# Check resource usage
docker stats
```

## 🚨 Troubleshooting

### Common Issues

#### 1. MISP Connection Failed
- Verify MISP URL is accessible from container
- Check API key validity
- Review network connectivity
- Check IRIS logs: `docker-compose logs app | grep -i misp`

#### 2. Database Connection Issues
- Verify PostgreSQL container is running
- Check database credentials in `.env`
- Review database logs: `docker-compose logs db`

#### 3. SSL/HTTPS Issues
- Ensure certificates are properly mounted
- Check nginx configuration
- Review nginx logs: `docker-compose logs nginx`

#### 4. Memory Issues
- Increase Docker memory allocation
- Monitor with `docker stats`
- Consider scaling worker containers

### Log Locations
- Application: `docker-compose logs app`
- Database: `docker-compose logs db`
- Nginx: `docker-compose logs nginx`
- Worker: `docker-compose logs worker`

## 🔒 Security Considerations

### Production Hardening
1. **Change all default passwords** in `.env`
2. **Use proper SSL certificates** (not self-signed)
3. **Implement firewall rules** (only expose necessary ports)
4. **Regular security updates** for base images
5. **API key rotation** (MISP, IRIS)
6. **Database access restrictions**
7. **Log monitoring and alerting**

### Network Security
- Place behind reverse proxy/load balancer
- Implement VPN access for admin functions
- Use separate networks for different tiers
- Monitor for suspicious access patterns

## 📞 Support

### Custom Features Support
- Threat Intel: Check MISP connectivity and API key
- SOAR: Verify integration credentials and endpoints
- Branding: Custom CSS/template modifications

### Getting Help
1. Check logs for specific error messages
2. Verify configuration in `.env` file
3. Test individual components (database, MISP, etc.)
4. Review `CUSTOM_FEATURES.md` for implementation details

## 📈 Performance Tuning

### Scaling Options
```yaml
# Scale worker containers
docker-compose -f docker-compose.production.yml up -d --scale worker=3

# Resource limits (add to docker-compose.production.yml)
services:
  app:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

### Database Optimization
- Increase PostgreSQL shared_buffers
- Configure proper connection pooling
- Regular VACUUM and ANALYZE operations
- Monitor query performance

## 🎯 Next Steps After Deployment

1. **Configure SOAR integrations** in Advanced → Integrations
2. **Set up Wazuh → Post Processor → IRIS** automation
3. **Create user accounts** and assign proper permissions
4. **Test Threat Intel submission** to MISP
5. **Configure notification settings**
6. **Set up regular backups**
7. **Implement monitoring and alerting**

---

**Deployment successful?** 🎉
Your Decian Custom IRIS platform should now be running with:
- Threat Intelligence integration ✅
- Enhanced branding ✅
- SOAR capabilities ✅
- Production-ready configuration ✅