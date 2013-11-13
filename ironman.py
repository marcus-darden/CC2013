#!/usr/bin/env python

'''Web front end for Computing Curricula 2013 Curriculum Exemplar (Ironman version).

Preconditions:
    environment - python 2 >= 2.7.3, flask, flask-sqlalchemy, gunicorn
'''
import os

from CC2013 import app


app.config['DEBUG'] = bool(os.environ.get('DEBUG', False))
app.config['SECRET_KEY'] = 'Computing Curricula 2013 Webapp'

if __name__ == '__main__':
    import logging
    logging.basicConfig()
    app.config['_LOGGING'] = logging
    app.run(host='0.0.0.0')
