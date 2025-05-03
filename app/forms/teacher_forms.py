from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange

class GradeForm(FlaskForm):
    comments = TextAreaField('Comentarios', validators=[Optional()])
    submit = SubmitField('Guardar Calificaciones')
    
    # Los campos para las calificaciones se añaden dinámicamente en la ruta

class FinalGradeForm(FlaskForm):
    value = FloatField('Calificación Final', validators=[DataRequired(), NumberRange(min=0, max=100)])
    comments = TextAreaField('Comentarios', validators=[Optional()])
    submit = SubmitField('Guardar Calificación Final')
