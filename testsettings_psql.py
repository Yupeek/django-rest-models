import copy

from testsettings import *

DATABASES = copy.deepcopy(DATABASES)
DATABASES['default'] = {
    'ENGINE': 'django.contrib.gis.db.backends.postgis',
    'NAME': 'django-rest-models',
    'USER': os.environ.get('PGUSER', 'yupeeposting'),
    'PASSWORD': os.environ.get('PGPASSWORD', 'yupeeposting'),
    'HOST': os.environ.get('PGHOST', 'yupeek-db1'),
    'PORT': os.environ.get('PGPORT', '5432'),
}
