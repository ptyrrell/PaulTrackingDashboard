# 🚀 Heroku Deployment Guide for Paul Tracking Dashboard

## Overview
This guide walks you through deploying your Django application to Heroku with a persistent PostgreSQL database.

## 📊 Database Architecture
- **Database**: PostgreSQL (managed by Heroku)
- **Persistence**: Full data persistence across deployments
- **Backups**: Automatic daily backups (on paid plans)
- **Updates**: Code updates DO NOT affect your database

## 🛠 Initial Setup

### 1. Install Heroku CLI
```bash
brew tap heroku/brew && brew install heroku
```

### 2. Login to Heroku
```bash
heroku login
```

### 3. Create Heroku App
```bash
heroku create paul-tracking-dashboard
# Or use any unique name you prefer
```

### 4. Add PostgreSQL Database
```bash
# For production (recommended - $5/month)
heroku addons:create heroku-postgresql:essential-0

# For testing (limited to 10K rows)
heroku addons:create heroku-postgresql:mini
```

### 5. Set Environment Variables
```bash
# Generate a secure secret key
heroku config:set SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(50))')

# Set Django settings module
heroku config:set DJANGO_SETTINGS_MODULE=settings_production

# Optional: Set debug level for troubleshooting
heroku config:set DJANGO_LOG_LEVEL=INFO
```

### 6. Deploy Your Code
```bash
# Add files to git
git add .
git commit -m "Add Heroku deployment configuration"

# Push to Heroku
git push heroku main
```

### 7. Create Superuser
```bash
heroku run python manage.py createsuperuser
```

### 8. Load Initial Data (Optional)
```bash
heroku run python manage.py loaddata fixtures/numbers.json
```

## 📦 Database Management

### Check Database Info
```bash
heroku pg:info
```

### Create Manual Backup
```bash
heroku pg:backups:capture
```

### List Backups
```bash
heroku pg:backups
```

### Download Backup
```bash
heroku pg:backups:download
```

### Restore from Backup
```bash
heroku pg:backups:restore b001 DATABASE_URL
```

## 🔄 Updating Your Application

### Safe Update Process
1. **Test locally first**
   ```bash
   python manage.py test
   ```

2. **Create database backup** (before major changes)
   ```bash
   heroku pg:backups:capture
   ```

3. **Deploy update**
   ```bash
   git add .
   git commit -m "Your update description"
   git push heroku main
   ```

4. **Migrations run automatically** via Procfile release command

5. **Verify deployment**
   ```bash
   heroku logs --tail
   heroku open
   ```

## 🔐 Database Security & Persistence

### What Persists:
- ✅ All user data
- ✅ All entered numbers, targets, cashflow
- ✅ User accounts and permissions
- ✅ Historical data and reports

### What Doesn't Affect Database:
- ✅ Code deployments
- ✅ Static file updates
- ✅ Configuration changes
- ✅ App restarts

### Automatic Backups (Essential Plan):
- Daily automatic backups
- 7 days retention
- Point-in-time recovery

## 🚨 Disaster Recovery

### If Something Goes Wrong:
1. **Check logs**
   ```bash
   heroku logs --tail
   ```

2. **Rollback code** (if needed)
   ```bash
   heroku rollback
   ```

3. **Restore database** (if needed)
   ```bash
   heroku pg:backups
   heroku pg:backups:restore b001 DATABASE_URL
   ```

## 💰 Cost Overview

### Recommended Setup:
- **Eco Dyno**: $5/month (app hosting)
- **Essential Database**: $5/month (1GB, automatic backups)
- **Total**: $10/month for production-ready setup

### Free Alternatives:
- Use external database (Neon, Supabase)
- Deploy to Railway or Render instead

## 🔧 Maintenance Commands

### View app status
```bash
heroku ps
```

### Restart app
```bash
heroku restart
```

### Run Django shell
```bash
heroku run python manage.py shell
```

### Run migrations manually
```bash
heroku run python manage.py migrate
```

### View database connection
```bash
heroku config:get DATABASE_URL
```

## 📱 Access Your App

After deployment:
- **App URL**: https://paul-tracking-dashboard.herokuapp.com
- **Admin Panel**: https://paul-tracking-dashboard.herokuapp.com/admin/

## 🆘 Troubleshooting

### Static files not loading?
```bash
heroku run python manage.py collectstatic --noinput
```

### Database connection issues?
```bash
heroku pg:diagnose
```

### Need more database space?
```bash
# Upgrade to Standard plan ($50/month, 64GB)
heroku addons:upgrade heroku-postgresql:standard-0
```

## 📝 Important Notes

1. **Database is separate from app** - Your data is safe during deployments
2. **Always backup before major changes** - Use `heroku pg:backups:capture`
3. **Monitor your row count** - Check with `heroku pg:info`
4. **Set up monitoring** - Use `heroku logs --tail` regularly
5. **Keep local backups** - Download backups periodically

## Support

For issues specific to this application, check:
- Repository: https://github.com/ptyrrell/PaulTrackingDashboard
- Heroku Status: https://status.heroku.com/
- Heroku Support: https://help.heroku.com/
