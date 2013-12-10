import os


basedir = os.path.abspath(os.path.dirname(__file__))

# General app config
DEBUG = bool(os.environ.get('DEBUG', False))
CSRF_ENABLED = True
SECRET_KEY = 'Computing Curricula 2013 Webapp'

# Database config
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_DATABASE_URI = 'postgresql://swudaeceketywb:MIzdh5zSVMNb7l5P46OIkRd2y7@ec2-54-204-24-154.compute-1.amazonaws.com/d3esdjt0vsa5je'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

# OpenID config
OPENID_PROVIDERS = [
    { 'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id' },
    { 'name': 'Yahoo', 'url': 'https://me.yahoo.com' },
    { 'name': 'AOL', 'url': 'http://openid.aol.com/<username>' },
    { 'name': 'Flickr', 'url': 'http://www.flickr.com/<username>' },
    { 'name': 'MyOpenID', 'url': 'https://www.myopenid.com' }]
