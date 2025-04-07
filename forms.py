from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, StringField
from wtforms.validators import InputRequired

class PlatformForm(FlaskForm):
    platform_file = TextAreaField('Edit Platform Config', validators=[InputRequired()])
    submit = SubmitField('Save')

#ADD VALIDATOR!!!

class LogForm(FlaskForm):
    delete = SubmitField('Clear Log')
    run = SubmitField('Test Run')


class ConfigForm(FlaskForm):
    key = StringField("Key", validators=[InputRequired()])
    client_secret = StringField("Client Secret", validators=[InputRequired()])
    submit = SubmitField('Save')

class EmailForm(FlaskForm):
    email_list = TextAreaField('Edit Emails', validators=[InputRequired()])
    submit = SubmitField('Save')