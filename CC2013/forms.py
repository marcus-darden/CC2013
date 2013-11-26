from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, TextAreaField
from wtforms.validators import Required, Length


__all__ = ['LoginForm', 'EditForm']


class LoginForm(Form):
    openid = TextField('OpenID:', validators=[Required()])
    remember_me = BooleanField('Remember Me', default=False)


class EditForm(Form):
    nickname = TextField('Nickname:', validators=[Required()])
    about_me = TextAreaField('About Me:', validators=[Length(min = 0, max = 140)])
