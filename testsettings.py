import django.conf.global_settings as DEFAULT_SETTINGS


SECRET_KEY = 'FAKEDKEYDONOUSEITINREALLIFE'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sq3',
    },
    'api': {
        'ENGINE': 'rest_models.backend',
        'NAME': 'http://localapi/api/v2/',
        'USER': 'userapi',
        'PASSWORD': 'passwordapi',
        'AUTH': 'rest_models.backend.auth.BasicAuth',
    },
    'api2': {
        'ENGINE': 'rest_models.backend',
        'NAME': 'http://localapi/api/v2/',
        'USER': 'userapi',
        'PASSWORD': 'passwordapi',
        'AUTH': 'rest_models.backend.auth.BasicAuth',
    },
    'TEST_api2': {
        'ENGINE': 'rest_models.backend',
        'NAME': 'http://127.0.0.1:8080/api/v2/',
        'USER': 'userapi',
        'PASSWORD': 'passwordapi',
        'AUTH': 'rest_models.backend.auth.BasicAuth',
    },
}

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

ROOT_URLCONF = 'testapi.urls'

DEBUG = True

STATIC_URL = '/static/'