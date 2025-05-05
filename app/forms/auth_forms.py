from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models.users import User

class LoginForm(FlaskForm):
    identification_number = StringField('Cédula de Identidad', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')

class RegistrationForm(FlaskForm):
    identification_number = StringField('Número de Cédula', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Nombre', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Apellido', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repetir Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')
    
    def validate_identification_number(self, identification_number):
        # Verificar si ya existe un usuario registrado con esta cédula
        user = User.query.filter_by(
            identification_number=identification_number.data,
            is_registered=True
        ).first()
        
        if user is not None:
            raise ValidationError('Esta cédula ya está registrada.')
    
    def validate_email(self, email):
        # Verificar si ya existe un usuario registrado con este email
        user = User.query.filter_by(email=email.data, is_registered=True).first()
        if user is not None:
            raise ValidationError('Este email ya está registrado.')
