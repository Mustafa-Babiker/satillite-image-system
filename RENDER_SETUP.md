# Render Deployment Setup Guide

## Service Details
- **Service ID**: srv-d915iqf7f7vs73d5gu8g
- **Service URL**: https://satillite-image-system.onrender.com
- **Repository**: https://github.com/Mustafa-Babiker/satillite-image-system

## Required Setup Steps in Render Dashboard

1. **Go to Render**: https://render.com/dashboard
2. **Select Service**: Find "satillite-image-system"
3. **Navigate to Settings > Environment**
4. **Add the following environment variables**:

```
MODEL_URL=https://github.com/Mustafa-Babiker/satillite-image-system/releases/download/v1.0.0/agri_unet.pth
SH_CLIENT_ID=5418b19c-c3ef-4ca5-ad90-c7a07db91a00
SH_CLIENT_SECRET=ltsA3OD82aKbZoflYQC5LAX527jJ0pUF
SECRET_KEY=your-secure-random-secret-key-here
DB_HOST=localhost
DB_NAME=agriculture_system
DB_USER=postgres
DB_PASSWORD=your-db-password
FLASK_ENV=production
```

5. **Save** and wait for auto-redeploy (2-3 minutes)

## Testing the Deployment

After variables are set and service restarts:

```bash
# Test the main page
curl https://satillite-image-system.onrender.com/

# The app should load the login page
```

## Auto-Deploy

- **Trigger**: Push code to `main` branch
- **Action**: GitHub Actions workflow triggers Render deploy
- **Time**: 2-3 minutes to see changes live

## Troubleshooting

- **Service not starting?** Check Render Logs (Dashboard > Logs tab)
- **Build errors?** Likely PyTorch install issues; check logs for details
- **Timeout errors?** Free tier cold boots may take time; wait longer or upgrade plan
- **Missing model?** Ensure `MODEL_URL` is set correctly and accessible
- **Database errors?** If using PostgreSQL, ensure `DB_*` variables are correct

## First Deployment Status

Initial deploy started at: 2026-06-29

Check logs at: https://render.com/dashboard/srv-d915iqf7f7vs73d5gu8g
