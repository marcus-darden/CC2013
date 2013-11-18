import os


basedir = os.path.abspath(os.path.dirname(__file__))

# General app config
DEBUG = bool(os.environ.get('DEBUG', False))
SECRET_KEY = 'Computing Curricula 2013 Webapp'

# Database config
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
