"""
Modelo de WSGI para PythonAnywhere.

No PythonAnywhere, copie este conteúdo para o arquivo WSGI indicado na aba Web.
Troque SEU_USUARIO_PYTHONANYWHERE pelo seu usuário real.
"""

import os
import sys


USERNAME = "SEU_USUARIO_PYTHONANYWHERE"
PROJECT_PATH = f"/home/{USERNAME}/sistema-gabinete-django"

if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_DEBUG", "false")
os.environ.setdefault(
    "DJANGO_ALLOWED_HOSTS",
    f"{USERNAME}.pythonanywhere.com,localhost,127.0.0.1",
)
os.environ.setdefault(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    f"https://{USERNAME}.pythonanywhere.com",
)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
