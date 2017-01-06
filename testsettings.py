import os


SECRET_KEY = 'FAKEDKEYDONOUSEITINREALLIFE'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sq3',
    },
    'api': {
        'ENGINE': 'rest_models.backend',
        'NAME': 'http://localapi/api/v2',
        'USER': 'admin',
        'PASSWORD': 'admin',
        'AUTH': 'rest_models.backend.auth.BasicAuth',
    },
    'apifail': {
        'ENGINE': 'rest_models.backend',
        'NAME': 'http://localapi/api/v1',
        'USER': 'admin',
        'PASSWORD': 'admin',
    },
    'api2': {
        'ENGINE': 'rest_models.backend',
        'NAME': 'http://localhost:8080/api/v2',
        'USER': 'userapi',
        'PASSWORD': 'passwordapi',
        'AUTH': 'rest_models.backend.auth.BasicAuth',
    },
    'TEST_api2': {
        'ENGINE': 'rest_models.backend',
        'NAME': 'http://localhost:8080/api/v2',
        'USER': 'userapi',
        'PASSWORD': 'passwordapi',
        'AUTH': 'rest_models.backend.auth.BasicAuth',
    },
}

ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

INSTALLED_APPS = (
    # Default Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # We test this one
    'testapp',
    'testapi',
    'rest_framework',
    'dynamic_rest',
) + (
    ('testapi.badapi', 'testapp.badapp')
    if os.environ.get('WITH_BADAPP', "false").lower().strip() == 'true'
    else tuple()
)

DATABASE_ROUTERS = [
    'rest_models.router.RestModelRouter',
]


MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

REST_FRAMEWORK = {
    'PAGE_SIZE': 10
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # insert your TEMPLATE_DIRS here
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
if os.environ.get('WITH_BADAPP', "false").lower().strip() == 'true':
    ROOT_URLCONF = 'testapi.badapi.urls'
else:
    ROOT_URLCONF = 'testapi.urls'


DEBUG = True

STATIC_URL = '/static/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        },
        'colored': {  # a nice colored format for terminal output
            'format': '\033[1;33m%(levelname)s\033[0m [\033[1;31m%(name)s'
                      '\033[0m:\033[1;32m%(lineno)s'
                      '\033[0m:\033[1;35m%(funcName)s\033[0m] \033[1;37m%(message)s\033[0m'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
