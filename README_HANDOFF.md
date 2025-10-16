# 🚀 Decian Custom IRIS - Production Handoff Package

## 📦 What's Included

This package contains a **production-ready Decian Custom IRIS platform** with enhanced features for SOC operations.

### 🎯 Key Features Added
- ✅ **Threat Intelligence Hub** - MISP integration for IOC sharing
- ✅ **Enhanced Branding** - "Ironclad Case Management" styling
- ✅ **SOAR Integrations** - SentinelOne, Velociraptor playbooks
- ✅ **Comprehensive Documentation** - Deployment guides and feature docs
- ✅ **Production Configuration** - Secure, scalable docker-compose setup

## 🚀 Quick Deployment

### For the Receiving Team:

1. **Extract this package** to your target server
2. **Copy environment template**: `cp .env.template .env`
3. **Edit `.env`** with your specific values (passwords, MISP API key, etc.)
4. **Deploy**: `docker-compose -f docker-compose.production.yml up -d`
5. **Access**: `https://localhost:443` (or your configured port)

### 📁 Important Files

| File | Purpose |
|------|---------|
| `DEPLOYMENT_GUIDE.md` | **START HERE** - Complete deployment instructions |
| `CUSTOM_FEATURES.md` | Technical documentation of all custom modifications |
| `docker-compose.production.yml` | Production-ready deployment configuration |
| `.env.template` | Configuration template (copy to `.env`) |
| `build-images.sh` | Build custom Docker images locally |
| `export-images.sh` | Export images for distribution |

## 🐳 Docker Images

### Pre-built Custom Images:
- `decian/iris-app:v2.4.22-custom` - Main application with all custom features
- `decian/iris-db:v2.4.22-custom` - PostgreSQL database
- `decian/iris-nginx:v2.4.22-custom` - Nginx reverse proxy

### If Images Need Building:
```bash
chmod +x build-images.sh
./build-images.sh
```

### If Images Need Exporting:
```bash
chmod +x export-images.sh
./export-images.sh
# Creates tar.gz files in ./exports/
```

## ⚙️ Critical Configuration

### 🔑 Required Before Deployment:

1. **Edit `.env` file** - Replace ALL placeholder values:
   ```bash
   POSTGRES_PASSWORD=your_secure_password
   IRIS_SECRET_KEY=your_32_char_secret_key
   MISP_API_KEY=your_misp_api_key
   ADMIN_PASSWORD=your_admin_password
   ```

2. **Verify MISP Access** - Ensure `https://misp.ironclad.decianx` is accessible

3. **Check Resource Requirements**:
   - Minimum: 4GB RAM, 20GB disk
   - Recommended: 8GB RAM, 50GB disk

## 🎯 Testing the Deployment

After deployment, verify these features work:

1. **Basic IRIS**: Login at `https://localhost:443`
2. **Threat Intel Tab**: Navigate to "Threat Intel" in left menu
3. **MISP Integration**: Submit a test IOC (e.g., IP address)
4. **SOAR Features**: Check Advanced → Integrations
5. **Enhanced Branding**: Verify "Ironclad Case Management" logo

## 🔧 Production Considerations

### Security Checklist:
- [ ] Changed all default passwords
- [ ] Using proper SSL certificates (not self-signed)
- [ ] Firewall configured (only expose port 443)
- [ ] MISP API key rotated and secured
- [ ] Database backups configured
- [ ] Log monitoring set up

### Performance Tuning:
- Scale workers: `docker-compose up -d --scale worker=3`
- Monitor resources: `docker stats`
- Check logs: `docker-compose logs -f`

## 📞 Support Information

### Architecture Overview:
```
Wazuh Agents → Post Processor → IRIS (Auto Case Creation)
                    ↓
IRIS ←→ MISP (Threat Intelligence Sharing)
  ↓
SentinelOne/Velociraptor (SOAR Response)
```

### Custom Code Locations:
- Threat Intel: `source/app/blueprints/threat_intel/`
- SOAR: `source/app/blueprints/soar/`
- Branding: `source/app/templates/includes/navigation*.html`

### If Something Breaks:
1. Check `DEPLOYMENT_GUIDE.md` troubleshooting section
2. Review logs: `docker-compose logs -f`
3. Verify configuration in `.env` file
4. Test MISP connectivity separately

## 🎉 Success Indicators

**You'll know it's working when:**
- IRIS loads at your configured URL
- "Threat Intel" tab appears in navigation
- IOC submission to MISP succeeds
- "Ironclad Case Management" branding shows correctly
- Demo data is visible (5 companies, 10 cases, 100 IOCs)

---

## 🚀 Ready to Deploy?

**Next Steps:**
1. Read `DEPLOYMENT_GUIDE.md` thoroughly
2. Configure your `.env` file
3. Run the deployment
4. Test the custom features
5. Integrate with your Wazuh setup

**Questions?** All technical details are documented in the included files.

**Good luck!** 🎯 You're deploying a world-class SOC platform.