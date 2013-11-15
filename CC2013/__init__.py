from flask import Flask


app = Flask(__name__)
app.config_from_object('config')

import CC2013.views
