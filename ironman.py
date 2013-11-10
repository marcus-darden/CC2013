#!/usr/bin/env python

'''Web front end for Computing Curricula 2013 Curriculum Exemplar (Ironman version).

Preconditions:
    environment - python 2 >= 2.7.3, flask, flask-sqlalchemy, gunicorn
'''
from CC2013 import app


app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'Computing Curricula 2013'

app.run(host='0.0.0.0')
