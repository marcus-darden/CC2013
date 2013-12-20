from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, TextAreaField
from wtforms.validators import Required, Length
from flask.ext.babel import gettext


__all__ = ['LoginForm', 'EditForm']


class LoginForm(Form):
    openid = TextField('OpenID:', validators=[Required()])
    remember_me = BooleanField(gettext('Remember Me'), default=False)


class EditForm(Form):
    nickname = TextField(gettext('Nickname:'), validators=[Required()])
    about_me = TextAreaField(gettext('About Me:'), validators=[Length(min = 0, max = 140)])

    def __init__(self, original_nickname, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.original_nickname = original_nickname

    def validate(self):
        # Inherited validation
        if not Form.validate(self):
            return False

        # Custom validation for unique nicknames
        if self.nickname.data == self.original_nickname:
            return True
        if self.nickname.data != User.make_valid_nickname(self.nickname.data):
            self.nickname.errors.append(gettext("This nickname has invalid "
                                                "characters. Please use "
                                                "letters, numbers, dots and "
                                                " underscores only."))
            return False
        user = User.query.filter_by(nickname=self.nickname.data).first()
        if user:
            self.nickname.errors.append(gettext('This nickname is already in use. Please choose another one.'))
            return False
        return True
