from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, DateField, FloatField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional, NumberRange
from app.models.users import User
from app.models.academic import AcademicYear, Grade, Section, Subject, Student, Teacher
from datetime import date

class UserForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Nombre', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Apellido', validators=[DataRequired(), Length(max=64)])
    role = SelectField('Rol', choices=[('admin', 'Administrador'), ('teacher', 'Profesor')], validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[Optional(), Length(min=6)])
    password2 = PasswordField('Repetir Contraseña', validators=[EqualTo('password')])
    specialization = StringField('Especialización', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Guardar')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None and user.id != getattr(self, 'user_id', None):
            raise ValidationError('Este nombre de usuario ya está en uso.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None and user.id != getattr(self, 'user_id', None):
            raise ValidationError('Este email ya está registrado.')

class AcademicYearForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(max=64)])
    start_date = DateField('Fecha de inicio', validators=[DataRequired()])
    end_date = DateField('Fecha de fin', validators=[DataRequired()])
    is_active = BooleanField('Activo')
    submit = SubmitField('Guardar')
    
    def validate_end_date(self, end_date):
        if end_date.data <= self.start_date.data:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')

class PeriodForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(max=64)])
    start_date = DateField('Fecha de inicio', validators=[DataRequired()])
    end_date = DateField('Fecha de fin', validators=[DataRequired()])
    academic_year_id = SelectField('Año académico', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Guardar')
    
    def validate_end_date(self, end_date):
        if end_date.data <= self.start_date.data:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')

class GradeForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(max=64)])
    level = StringField('Nivel', validators=[DataRequired(), Length(max=64)])
    submit = SubmitField('Guardar')

class SectionForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(max=10)])
    grade_id = SelectField('Grado', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Guardar')

class SubjectForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    code = StringField('Código', validators=[DataRequired(), Length(max=20)])
    grades = SelectField('Grados', coerce=int, validators=[DataRequired()], multiple=True)
    submit = SubmitField('Guardar')

class StudentForm(FlaskForm):
    first_name = StringField('Nombre', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Apellido', validators=[DataRequired(), Length(max=64)])
    student_id = StringField('Cédula', validators=[DataRequired(), Length(max=20)])  # Este campo se usará como cédula
    birth_date = DateField('Fecha de nacimiento', validators=[Optional()])
    gender = SelectField('Género', choices=[('M', 'Masculino'), ('F', 'Femenino')], validators=[Optional()])
    address = StringField('Dirección', validators=[Optional(), Length(max=200)])
    phone = StringField('Teléfono', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    section_id = SelectField('Sección', coerce=int, validators=[DataRequired()])
    is_active = BooleanField('Activo', default=True)
    submit = SubmitField('Guardar')
    
    def validate_student_id(self, student_id):
        student = Student.query.filter_by(student_id=student_id.data).first()
        if student is not None and student.id != getattr(self, 'student_id_db', None):
            raise ValidationError('Esta cédula ya está registrada.')

class StudentGradeForm(FlaskForm):
    value = FloatField('Calificación', validators=[DataRequired(), NumberRange(min=0, max=100)])
    comments = StringField('Comentarios', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Guardar')

class FinalGradeForm(FlaskForm):
    value = FloatField('Calificación Final', validators=[DataRequired(), NumberRange(min=0, max=100)])
    comments = StringField('Comentarios', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Guardar')

class TeacherPreRegistrationForm(FlaskForm):
    identification_number = StringField('Número de Cédula', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Nombre', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Apellido', validators=[DataRequired(), Length(max=64)])
    specialization = StringField('Especialización', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Pre-Registrar Profesor')
    
    def validate_identification_number(self, identification_number):
        user = User.query.filter_by(identification_number=identification_number.data).first()
        if user is not None:
            raise ValidationError('Esta cédula ya está registrada.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Este email ya está registrado.')

class TeacherForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Nombre', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Apellido', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Contraseña', validators=[Optional(), Length(min=6)])
    password2 = PasswordField('Repetir Contraseña', validators=[EqualTo('password')])
    specialization = StringField('Especialización', validators=[Optional(), Length(max=100)])
    qualification = StringField('Calificación/Título', validators=[Optional(), Length(max=100)])
    phone = StringField('Teléfono', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Guardar')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None and getattr(self, 'teacher_id', None) != getattr(user.teacher_profile, 'id', None):
            raise ValidationError('Este nombre de usuario ya está en uso.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None and getattr(self, 'teacher_id', None) != getattr(user.teacher_profile, 'id', None):
            raise ValidationError('Este email ya está registrado.')

class TeacherAssignmentForm(FlaskForm):
    teacher_id = SelectField('Profesor', coerce=int, validators=[DataRequired()])
    subject_id = SelectField('Asignatura', coerce=int, validators=[DataRequired()])
    section_id = SelectField('Sección', coerce=int, validators=[DataRequired()])
    academic_year_id = SelectField('Año académico', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Guardar')
    
    def __init__(self, *args, **kwargs):
        super(TeacherAssignmentForm, self).__init__(*args, **kwargs)
        self.teacher_id.choices = [(t.id, f"{t.user.last_name}, {t.user.first_name}") for t in Teacher.query.join(User).order_by(User.last_name, User.first_name).all()]
        self.subject_id.choices = [(s.id, f"{s.name} ({s.code})") for s in Subject.query.order_by(Subject.name).all()]
        self.section_id.choices = [(s.id, f"{s.grade.name} '{s.name}'") for s in Section.query.join(Grade).order_by(Grade.level, Grade.name, Section.name).all()]
        self.academic_year_id.choices = [(a.id, a.name) for a in AcademicYear.query.order_by(AcademicYear.start_date.desc()).all()]

class GradeTypeForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(max=64)])
    weight = FloatField('Peso', validators=[DataRequired(), NumberRange(min=0.1)])
    subject_id = SelectField('Asignatura', coerce=int, validators=[DataRequired()])
    period_id = SelectField('Período', coerce=int, validators=[DataRequired()])
    teacher_id = SelectField('Profesor', coerce=int, validators=[DataRequired()])
    grade_id = SelectField('Grado', coerce=int, validators=[DataRequired()])
    section_id = SelectField('Sección', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Guardar')

class SettingsForm(FlaskForm):
    school_name = StringField('Nombre de la Institución', validators=[DataRequired(), Length(max=100)])
    school_address = StringField('Dirección', validators=[Length(max=200)])
    school_phone = StringField('Teléfono', validators=[Length(max=20)])
    school_email = StringField('Email', validators=[Email(), Length(max=100)])
    passing_grade = IntegerField('Nota de Aprobación', validators=[DataRequired(), NumberRange(min=0, max=100)])
    submit = SubmitField('Guardar Configuración')