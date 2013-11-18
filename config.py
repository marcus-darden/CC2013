import os


_basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = bool(os.environ.get('DEBUG', False))
SECRET_KEY = 'Computing Curricula 2013 Webapp'
