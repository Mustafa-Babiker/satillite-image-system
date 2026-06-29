# Satellite Image System

Flask-based satellite image analysis system using Sentinel Hub and a segmentation model.

## What is included

- `app.py`: Flask application with login/system routes and Sentinel Hub download + analysis.
- `templates/`, `static/`: frontend HTML/CSS assets.
- `requirements.txt`: Python dependencies.
- `render.yaml`: Render deployment configuration.
- `Procfile`: startup command for Render / Heroku-style hosts.
- `.env.example`: environment variable template.

## Local setup

1. Copy `.env.example` to `.env`:

```bash
cd "c:/Users/Mustafa Babiker/Desktop/satillite image system/the system"
copy .env.example .env
```

2. Fill in your settings in `.env`.

3. Install dependencies:

```bash
pip install -r requirements.txt -f https://download.pytorch.org/whl/cpu
```

4. Run locally:

```bash
gunicorn app:app --workers 2 --bind 0.0.0.0:8000
```

5. Open browser at `http://127.0.0.1:8000`.

## Render deployment

This repository is connected to Render for automatic deployment.

### Environment Variables (set in Render dashboard)

Go to **Services → satillite-image-system → Settings → Environment** and add:

```
MODEL_URL=https://github.com/Mustafa-Babiker/satillite-image-system/releases/download/v1.0.0/agri_unet.pth
SH_CLIENT_ID=<your_sentinel_hub_id>
SH_CLIENT_SECRET=<your_sentinel_hub_secret>
SECRET_KEY=<secure-random-key>
DB_HOST=<database_host>
DB_NAME=agriculture_system
DB_USER=<database_user>
DB_PASSWORD=<database_password>
FLASK_ENV=production
```

### Auto Deploy

- Push to `main` branch → GitHub Actions triggers Render deploy via webhook.
- Render pulls latest code and auto-restarts the app.
- Monitor logs at Render dashboard.

## Notes

- The app loads environment variables from `.env` locally.
- `.env` is ignored by Git and should not be committed.
- The model file `agri_unet.pth` can be placed in the repository root, or you can provide `MODEL_URL` to download it at startup.
- If you do not use PostgreSQL in Render, you may need to adjust the DB settings or disable the database functionality.
