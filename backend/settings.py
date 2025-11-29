from pathlib import Path

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Security key (development only)
SECRET_KEY = 'django-insecure-your-secret-key'

# Development mode
DEBUG = True

# Allowed hosts for development
ALLOWED_HOSTS = []


# ---------------------- INSTALLED APPS ---------------------- #

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'corsheaders',

    # Local apps
    'tasks',
]


# ---------------------- MIDDLEWARE -------------------------- #

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',   # Must be at top
    'django.middleware.common.CommonMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ---------------------- URL CONFIG --------------------------- #

ROOT_URLCONF = 'backend.urls'


# ---------------------- TEMPLATES (REQUIRED) ----------------- #

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Look for templates in the frontend folder
        'DIRS': [ BASE_DIR / 'frontend' ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]



# ---------------------- WSGI ------------------------------- #

WSGI_APPLICATION = 'backend.wsgi.application'


# ---------------------- DATABASE (SQLite) ------------------- #

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ---------------------- PASSWORD VALIDATION ---------------- #

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ---------------------- LANGUAGE & TIME ---------------------- #

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ---------------------- STATIC FILES ------------------------ #

STATIC_URL = 'static/'


# ---------------------- CORS SETTINGS ------------------------ #

CORS_ALLOW_ALL_ORIGINS = True   # Only for development


# ---------------------- DEFAULT PK FIELD ---------------------- #

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
