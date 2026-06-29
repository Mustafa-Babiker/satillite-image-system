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

This repository contains `render.yaml` and `Procfile` for Render.

- Create a new GitHub repository and push the code.
- Connect the repository to Render.
- Add the required environment variables in Render dashboard:
  - `SECRET_KEY`
  - `SH_CLIENT_ID`
  - `SH_CLIENT_SECRET`
  - `DB_HOST`
  - `DB_NAME`
  - `DB_USER`
  - `DB_PASSWORD`

Render will deploy automatically on new pushes.

## Notes

- The app loads environment variables from `.env` locally.
- `.env` is ignored by Git and should not be committed.
- The model file `agri_unet.pth` can be placed in the repository root, or you can provide `MODEL_URL` to download it at startup.
- If you do not use PostgreSQL in Render, you may need to adjust the DB settings or disable the database functionality.
