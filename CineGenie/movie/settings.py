# Static files configuration
STATIC_URL = '/static/'

# Define directories where Django will look for static files
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Directory where static files will be collected to during collectstatic
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') 