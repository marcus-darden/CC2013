from flask.ext.wtf import Form
from wtforms import TextField, BooleanField
from wtforms.validators import Required


__all__ = ['LoginForm']


class LoginForm(Form):
    openid = TextField('openid', validators=[Required()])
    remember_me = BooleanField('remember_me', default=False)
