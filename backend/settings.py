# backend/settings.py
import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY & DEBUG from environment (safe for production)
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key")
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

# ALLOWED_HOSTS — set via env var (comma separated) or allow all for testing
_allowed = os.environ.get("ALLOWED_HOSTS", "*")
if _allowed.strip() == "":
    ALLOWED_HOSTS = []
else:
    ALLOWED_HOSTS = [h.strip() for h in _allowed.split(",") if h.strip()]

# CSRF trusted origins (optional)
_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
if _csrf:
    CSRF_TRUSTED_ORIGINS = [u.strip() for u in _csrf.split(",") if u.strip()]

# APPLICATIONS
INSTALLED_APPS = [
    # django defaults
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # third-party
    "corsheaders",

    # your app
    "tasks",
]

# MIDDLEWARE (WhiteNoise added)
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",

    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serve static files
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates", BASE_DIR / "frontend", ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

# ----------------------
# DATABASES (smart fallback)
# ----------------------
# Priority:
# 1) If DATABASE_URL is provided, use dj_database_url to parse it (Postgres on Render or other)
# 2) If running on Render (RENDER env var present), use Render Disk SQLite path
# 3) Fallback to local BASE_DIR / 'db.sqlite3' for development

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=False)
    }
else:
    # When deployed on Render with a disk mounted we prefer a path under the disk:
    # Render disk mount we recommended: /opt/render/project/src/dbdata
    if "RENDER" in os.environ:
        # use sqlite on the render disk (persistent)
        db_path = "/opt/render/project/src/dbdata/db.sqlite3"
    else:
        # local dev fallback
        db_path = str(BASE_DIR / "db.sqlite3")

    # ensure directory exists
    db_dir = os.path.dirname(db_path)
    try:
        os.makedirs(db_dir, exist_ok=True)
    except Exception:
        # If this fails, it's non-fatal; sqlite will attempt to create file when opening
        pass

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": db_path,
        }
    }

# Password validation (defaults)
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("TIME_ZONE", "UTC")
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (WhiteNoise)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Optional: serve frontend build folder too if you keep index.html in frontend
STATICFILES_DIRS = [BASE_DIR / "frontend"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS (allow all origins for testing; change to allowed list in production)
CORS_ALLOW_ALL_ORIGINS = os.environ.get("CORS_ALLOW_ALL_ORIGINS", "True").lower() in ("true", "1", "yes")

# Logging (basic)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO")},
}
