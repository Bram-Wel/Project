from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User

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

    def __init__(self, formdata, **kwargs):
        super().__init__(formdata, **kwargs)
        if not self.device_type.data:
            self.device_type.data = 'default'

class CreateUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Email()])
    title = StringField('Title', validators=[Length(max=64)], render_kw={"placeholder": "Organisation"})
    role = SelectField('Role', choices=[('CUSTOMER_USER', 'Customer User'), ('CUSTOMER_ADMIN', 'Customer Admin')], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Create User')

    def validate(self, **kwargs):
        if not super().validate(**kwargs):
            return False
        user = User.query.filter_by(username=self.username.data).first()
        if user:
            self.username.errors.append('Please use a different email address.')
            return False
        if not self.title.data:
            self.title.data = self.username.data
        return True