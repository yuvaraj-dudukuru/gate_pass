# Deployment Guide for Render.com

This guide will help you deploy the Gatepass Django application to Render.com.

## Prerequisites

1. A GitHub account with your code pushed to a repository
2. A Render.com account (free tier available)
3. Your project should be ready with all changes committed

## Project Structure

The project has the following structure:
```
Gatepass nov2/
├── Gatepass/              # Django project root
│   ├── hostel_gatepass/   # Django settings module
│   ├── gatepass/          # Main app
│   ├── manage.py
│   └── requirements.txt
├── Procfile              # For Render deployment
└── render.yaml           # Alternative Render config
```

## Deployment Steps

### Option 1: Using Procfile (Recommended)

1. **Connect Repository to Render**
   - Log in to [Render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository containing this project

2. **Configure the Service**
   - **Name**: Choose a name (e.g., "gatepass-django")
   - **Environment**: Python 3
   - **Build Command**: `cd Gatepass && pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command**: `cd Gatepass && gunicorn hostel_gatepass.wsgi:application --bind 0.0.0.0:$PORT`
   - **Plan**: Select Free or Paid plan

3. **Set Environment Variables**
   Click "Advanced" → "Add Environment Variable" and add:
   
   - `DEBUG`: `False`
   - `SECRET_KEY`: Generate a secure random key (you can use: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
   - `ALLOWED_HOSTS`: `.onrender.com` (or your specific domain)
   - `DATABASE_URL`: (If using Render PostgreSQL, this will be auto-provided)

4. **Database Setup (Optional)**
   - If you need a database, create a PostgreSQL database in Render
   - Render will automatically provide the `DATABASE_URL` environment variable
   - The app will automatically use it via `dj-database-url`

5. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy your application
   - Monitor the logs for any issues

### Option 2: Using render.yaml

If you prefer using the `render.yaml` file:

1. **Push render.yaml to your repository** (already included)
2. **In Render Dashboard**:
   - Click "New +" → "Blueprint"
   - Connect your repository
   - Render will automatically detect and use `render.yaml`

## Environment Variables Reference

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `DEBUG` | Enable/disable debug mode | `False` (production) |
| `SECRET_KEY` | Django secret key | Auto-generated secure key |
| `ALLOWED_HOSTS` | Allowed host domains | `.onrender.com` |
| `DATABASE_URL` | Database connection string | Auto-provided by Render PostgreSQL |

## Post-Deployment Checklist

- [ ] Verify the application is accessible at your Render URL
- [ ] Check that static files are loading correctly
- [ ] Test user registration and login
- [ ] Verify database migrations ran successfully
- [ ] Check application logs for any errors
- [ ] Test all major features of the application

## Troubleshooting

### Static Files Not Loading
- Ensure `collectstatic` ran during build (check build logs)
- Verify `STATIC_ROOT` is set correctly in `settings.py`
- Check that WhiteNoise middleware is in `MIDDLEWARE`

### Database Connection Issues
- Verify `DATABASE_URL` is set correctly
- Check that `dj-database-url` is in `requirements.txt`
- Ensure database migrations ran: `python manage.py migrate`

### Application Won't Start
- Check the logs in Render dashboard
- Verify `Procfile` or `render.yaml` has correct paths
- Ensure all dependencies are in `requirements.txt`
- Check that `SECRET_KEY` is set

### CORS Errors (if using API)
- Update `CORS_ALLOWED_ORIGINS` in `settings.py` with your frontend domain
- Ensure `CORS_ALLOW_ALL_ORIGINS = False` in production

## Local Testing Before Deployment

Before deploying, test the production setup locally:

```bash
# Set production-like environment variables
export DEBUG=False
export SECRET_KEY="your-secret-key-here"

# Collect static files
cd Gatepass
python manage.py collectstatic --noinput

# Test with Gunicorn
gunicorn hostel_gatepass.wsgi:application --bind 0.0.0.0:8000
```

## Additional Notes

- The project uses **WhiteNoise** for static file serving in production
- **Gunicorn** is configured as the WSGI server
- Database migrations run automatically during build (via `render.yaml`)
- The app is configured to use PostgreSQL when `DATABASE_URL` is provided, otherwise falls back to SQLite

## Security Considerations

- ✅ `DEBUG=False` in production
- ✅ `SECRET_KEY` from environment variable
- ✅ SSL/HTTPS enforced (via security settings)
- ✅ CORS restricted in production
- ✅ Secure cookies enabled in production

## Support

For issues specific to:
- **Render.com**: Check [Render Documentation](https://render.com/docs)
- **Django Deployment**: See [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)

