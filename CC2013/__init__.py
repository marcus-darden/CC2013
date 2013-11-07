#!/usr/bin/env python

'''Web front end for Computing Curricula 2013 Curriculum Exemplar (Ironman version).

Preconditions:
    environment - python 2 >= 2.7.3, flask, flask-sqlalchemy, gunicorn
'''
from flask import Flask


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'Computing Curricula 2013'

import CC2013.views
import CC2013.models

if __name__ == '__main__':
    app.run()
