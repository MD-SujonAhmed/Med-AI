import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MedAi.settings')

application = get_wsgi_application()

# Vercel expects `app` or `handler`
app = application
handler = application
# Print("Hello World")