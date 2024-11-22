from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class DeviceForm(FlaskForm):
    device_name = StringField('Device Name', validators=[DataRequired()])
    device_type = StringField('Device Type', validators=[DataRequired()])
    device_label = StringField('Device Label')
    device_description = StringField('Device Description')
    submit = SubmitField('Add Device')

    def __init__(self, formdata=..., **kwargs):
        super().__init__(formdata, **kwargs)
        self.device_type.data = 'default'

class CreateUserForm(FlaskForm):
    id = StringField('ID', validators=[DataRequired(), Length(min=1, max=64)])
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=64)])
    role = StringField('Role', validators=[DataRequired(), Length(min=1, max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Create User')

    def validate_role(self, field):
        if field.data.upper() not in ["CUSTOMER_ADMIN", "CUSTOMER_USER"]:
            raise ValidationError("Invalid role. Must be CUSTOMER_ADMIN or CUSTOMER_USER")