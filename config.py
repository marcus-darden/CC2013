# -*- coding: utf-8 -*-

import os
from base64 import b64decode


basedir = os.path.abspath(os.path.dirname(__file__))

# General flask config
DEBUG = bool(os.environ.get('DEBUG', False))
CSRF_ENABLED = True
SECRET_KEY = 'Computing Curricula 2013 Webapp'

# Database config
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
                                         'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
WHOOSH_BASE = os.path.join(basedir, 'search.db')
SQLALCHEMY_RECORD_QUERIES = True
DATABASE_QUERY_TIMEOUT = 0.5  # slow database query threshold (in seconds)

# OpenID config
OPENID_PROVIDERS = [
    { 'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id' },
    { 'name': 'Yahoo', 'url': 'https://me.yahoo.com' },
    { 'name': 'AOL', 'url': 'http://openid.aol.com/<username>' },
    { 'name': 'Flickr', 'url': 'http://www.flickr.com/<username>' },
    { 'name': 'MyOpenID', 'url': 'https://www.myopenid.com' }]

# email server
MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = 'ontoral@gmail.com'
MAIL_PASSWORD = b64decode(os.environ.get('RANDOMIZER', 'password'))

# administrator list
ADMINS = ['on.toral@gmail.com']

# Other config
PROGRAMS_PER_PAGE = 10

# available languages
LANGUAGES = {
    'en': 'English',
    'es': 'Español'
}
