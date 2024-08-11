"""
WSGI config for SS2DTournamentRunner project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os
from dotenv import load_dotenv


from django.core.wsgi import get_wsgi_application

# add DOTENV_PATH to the user environ : DOTENV_PATH.
DOTENV_PATH = os.path.join(os.path.dirname(__file__), '.env')
if os.path.isfile(DOTENV_PATH):
    load_dotenv(DOTENV_PATH)
os.environ['DJ_DOTENV_PATH'] = DOTENV_PATH

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SS2DTournamentRunner.settings')
# os.environ['HTTPS'] = "on" # production with SSL only

application = get_wsgi_application()
