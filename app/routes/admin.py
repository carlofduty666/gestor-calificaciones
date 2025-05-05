from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from io import BytesIO
import pandas as pd
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, BooleanField, PasswordField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, ValidationError
from app.models.users import User
from app.models.academic import AcademicYear, Period, Grade, Section, Subject, Student, Teacher, TeacherAssignment, Admin
from app.models.grades import GradeType, StudentGrade, FinalGrade
from app.forms.admin_forms import UserForm, AcademicYearForm, PeriodForm, GradeForm, SectionForm, SubjectForm, StudentForm, TeacherForm, TeacherAssignmentForm, SettingsForm, GradeTypeForm, StudentGradeForm, FinalGradeForm, TeacherPreRegistrationForm
from app import db

admin = Blueprint('admin', __name__)

@admin.before_request
def check_admin():
    if not current_user.is_authenticated or not current_user.is_admin():
        flash('Acceso no autorizado. Se requieren privilegios de administrador.', 'danger')
        return redirect(url_for('auth.login'))

@admin.route('/dashboard')
@login_required
def dashboard():
    # Estadísticas para el dashboard
    stats = {
        'students': Student.query.filter_by(is_active=True).count(),
        'teachers': Teacher.query.count(),
        'subjects': Subject.query.count(),
        'grades': Grade.query.count()
    }
    
    # Año académico activo
    active_year = AcademicYear.query.filter_by(is_active=True).first()
    
    return render_template('admin/dashboard.html', title='Panel de Administración', stats=stats, active_year=active_year)

# Rutas para gestión de usuarios
@admin.route('/users')
@login_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', title='Gestión de Usuarios', users=users)

@admin.route('/users/new', methods=['GET', 'POST'])
@login_required
def new_user():
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        
        # Si es profesor, crear perfil de profesor
        if form.role.data == 'teacher':
            teacher = Teacher(user=user, specialization=form.specialization.data)
            db.session.add(teacher)
            
        db.session.commit()
        flash('Usuario creado correctamente', 'success')
        return redirect(url_for('admin.users'))
        
    return render_template('admin/user_form.html', title='Nuevo Usuario', form=form)

@admin.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    user = User.query.get_or_404(id)
    form = UserForm(obj=user)
    
    # No permitir cambiar el rol si es el único administrador
    if user.is_admin() and User.query.filter_by(role='admin').count() == 1:
        form.role.render_kw = {'disabled': 'disabled'}
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        
        # Solo cambiar el rol si no es el único administrador
        if not (user.is_admin() and User.query.filter_by(role='admin').count() == 1):
            user.role = form.role.data
        
        if form.password.data:
            user.set_password(form.password.data)
            
        # Actualizar o crear perfil de profesor
        if user.role == 'teacher':
            if user.teacher_profile:
                user.teacher_profile.specialization = form.specialization.data
            else:
                teacher = Teacher(user=user, specialization=form.specialization.data)
                db.session.add(teacher)
                
        db.session.commit()
        flash('Usuario actualizado correctamente', 'success')
        return redirect(url_for('admin.users'))
        
    # Si es profesor, cargar especialización
    if user.teacher_profile:
        form.specialization.data = user.teacher_profile.specialization
        
    return render_template('admin/user_form.html', title='Editar Usuario', form=form, user=user)

@admin.route('/users/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    user = User.query.get_or_404(id)
    
    # No permitir eliminar el último administrador
    if user.is_admin() and User.query.filter_by(role='admin').count() == 1:
        flash('No se puede eliminar el único usuario administrador', 'danger')
        return redirect(url_for('admin.users'))
        
    # No permitir eliminar al usuario actual
    if user.id == current_user.id:
        flash('No puedes eliminar tu propio usuario', 'danger')
        return redirect(url_for('admin.users'))
        
    db.session.delete(user)
    db.session.commit()
    flash('Usuario eliminado correctamente', 'success')
    return redirect(url_for('admin.users'))

# Rutas para gestión de años académicos
@admin.route('/academic-years')
@login_required
def academic_years():
    years = AcademicYear.query.all()
    return render_template('admin/academic_years.html', title='Años Académicos', years=years)

@admin.route('/academic-years/new', methods=['GET', 'POST'])
@login_required
def new_academic_year():
    form = AcademicYearForm()
    if form.validate_on_submit():
        # Si se marca como activo, desactivar los demás
        if form.is_active.data:
            AcademicYear.query.update({AcademicYear.is_active: False})
            
        year = AcademicYear(
            name=form.name.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            is_active=form.is_active.data
        )
        db.session.add(year)
        db.session.commit()
        flash('Año académico creado correctamente', 'success')
        return redirect(url_for('admin.academic_years'))
        
    return render_template('admin/academic_year_form.html', title='Nuevo Año Académico', form=form)

# Rutas para gestión de períodos académicos
@admin.route('/periods')
@login_required
def periods():
    periods = Period.query.all()
    return render_template('admin/periods.html', title='Períodos Académicos', periods=periods)

@admin.route('/periods/new', methods=['GET', 'POST'])
@login_required
def new_period():
    form = PeriodForm()
    # Cargar años académicos para el select
    form.academic_year_id.choices = [(y.id, y.name) for y in AcademicYear.query.all()]
    
    if form.validate_on_submit():
        period = Period(
            name=form.name.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            academic_year_id=form.academic_year_id.data,
            weight=form.weight.data
        )
        db.session.add(period)
        db.session.commit()
        flash('Período académico creado correctamente', 'success')
        return redirect(url_for('admin.periods'))
        
    return render_template('admin/period_form.html', title='Nuevo Período', form=form)

@admin.route('/periods/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_period(id):
    period = Period.query.get_or_404(id)
    form = PeriodForm(obj=period)
    form.academic_year_id.choices = [(y.id, y.name) for y in AcademicYear.query.all()]
    
    if form.validate_on_submit():
        period.name = form.name.data
        period.start_date = form.start_date.data
        period.end_date = form.end_date.data
        period.academic_year_id = form.academic_year_id.data
        period.weight = form.weight.data
        
        db.session.commit()
        flash('Período académico actualizado correctamente', 'success')
        return redirect(url_for('admin.periods'))
        
    return render_template('admin/period_form.html', title='Editar Período', form=form)

@admin.route('/periods/<int:id>/delete', methods=['POST'])
@login_required
def delete_period(id):
    period = Period.query.get_or_404(id)
    
    # Verificar si hay calificaciones asociadas a este período
    if StudentGrade.query.filter_by(period_id=id).first() or FinalGrade.query.filter_by(period_id=id).first():
        flash('No se puede eliminar este período porque tiene calificaciones asociadas', 'danger')
        return redirect(url_for('admin.periods'))
    
    db.session.delete(period)
    db.session.commit()
    flash('Período académico eliminado correctamente', 'success')
    return redirect(url_for('admin.periods'))

# Rutas para gestión de grados
@admin.route('/grades')
@login_required
def grades():
    grades = Grade.query.all()
    return render_template('admin/grades.html', title='Grados', grades=grades)

@admin.route('/grades/new', methods=['GET', 'POST'])
@login_required
def new_grade():
    form = GradeForm()
    if form.validate_on_submit():
        grade = Grade(
            name=form.name.data,
            level=form.level.data,
            description=form.description.data
        )
        db.session.add(grade)
        db.session.commit()
        flash('Grado creado correctamente', 'success')
        return redirect(url_for('admin.grades'))
        
    return render_template('admin/grades.html', title='Nuevo Grado', form=form)

@admin.route('/grades/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_grade(id):
    grade = Grade.query.get_or_404(id)
    form = GradeForm(obj=grade)
    
    if form.validate_on_submit():
        grade.name = form.name.data
        grade.level = form.level.data
        grade.description = form.description.data
        
        db.session.commit()
        flash('Grado actualizado correctamente', 'success')
        return redirect(url_for('admin.grades'))
        
    return render_template('admin/grade_form.html', title='Editar Grado', form=form)

@admin.route('/grades/<int:id>/delete', methods=['POST'])
@login_required
def delete_grade(id):
    grade = Grade.query.get_or_404(id)
    
    # Verificar si hay secciones asociadas a este grado
    if Section.query.filter_by(grade_id=id).first():
        flash('No se puede eliminar este grado porque tiene secciones asociadas', 'danger')
        return redirect(url_for('admin.grades'))
    
    db.session.delete(grade)
    db.session.commit()
    flash('Grado eliminado correctamente', 'success')
    return redirect(url_for('admin.grades'))

# Rutas para gestión de secciones
@admin.route('/sections')
@login_required
def sections():
    sections = Section.query.all()
    return render_template('admin/sections.html', title='Secciones', sections=sections)

@admin.route('/sections/new', methods=['GET', 'POST'])
@login_required
def new_section():
    form = SectionForm()
    form.grade_id.choices = [(g.id, g.name) for g in Grade.query.order_by(Grade.level).all()]
    
    if form.validate_on_submit():
        section = Section(
            name=form.name.data,
            grade_id=form.grade_id.data,
            capacity=form.capacity.data
        )
        db.session.add(section)
        db.session.commit()
        flash('Sección creada correctamente', 'success')
        return redirect(url_for('admin.sections'))
        
    return render_template('admin/section_form.html', title='Nueva Sección', form=form)

@admin.route('/sections/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_section(id):
    section = Section.query.get_or_404(id)
    form = SectionForm(obj=section)
    form.grade_id.choices = [(g.id, g.name) for g in Grade.query.order_by(Grade.level).all()]
    
    if form.validate_on_submit():
        section.name = form.name.data
        section.grade_id = form.grade_id.data
        section.capacity = form.capacity.data
        
        db.session.commit()
        flash('Sección actualizada correctamente', 'success')
        return redirect(url_for('admin.sections'))
        
    return render_template('admin/section_form.html', title='Editar Sección', form=form)

@admin.route('/sections/<int:id>/delete', methods=['POST'])
@login_required
def delete_section(id):
    section = Section.query.get_or_404(id)
    
    # Verificar si hay estudiantes asociados a esta sección
    if Student.query.filter_by(section_id=id).first():
        flash('No se puede eliminar esta sección porque tiene estudiantes asociados', 'danger')
        return redirect(url_for('admin.sections'))
    
    # Verificar si hay asignaciones de profesores a esta sección
    if TeacherAssignment.query.filter_by(section_id=id).first():
        flash('No se puede eliminar esta sección porque tiene asignaciones de profesores', 'danger')
        return redirect(url_for('admin.sections'))
    
    db.session.delete(section)
    db.session.commit()
    flash('Sección eliminada correctamente', 'success')
    return redirect(url_for('admin.sections'))

# Rutas para gestión de asignaturas
@admin.route('/subjects')
@login_required
def subjects():
    subjects = Subject.query.all()
    return render_template('admin/subjects.html', title='Asignaturas', subjects=subjects)

@admin.route('/subjects/new', methods=['GET', 'POST'])
@login_required
def new_subject():
    form = SubjectForm()
    
    if form.validate_on_submit():
        subject = Subject(
            name=form.name.data,
            code=form.code.data,
            description=form.description.data,
            credits=form.credits.data
        )
        db.session.add(subject)
        db.session.commit()
        flash('Asignatura creada correctamente', 'success')
        return redirect(url_for('admin.subjects'))
        
    return render_template('admin/subject_form.html', title='Nueva Asignatura', form=form)

@admin.route('/subjects/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_subject(id):
    subject = Subject.query.get_or_404(id)
    form = SubjectForm(obj=subject)
    
    if form.validate_on_submit():
        subject.name = form.name.data
        subject.code = form.code.data
        subject.description = form.description.data
        subject.credits = form.credits.data
        
        db.session.commit()
        flash('Asignatura actualizada correctamente', 'success')
        return redirect(url_for('admin.subjects'))
        
    return render_template('admin/subject_form.html', title='Editar Asignatura', form=form)

@admin.route('/subjects/<int:id>/delete', methods=['POST'])
@login_required
def delete_subject(id):
    subject = Subject.query.get_or_404(id)
    
    # Verificar si hay asignaciones de profesores a esta asignatura
    if TeacherAssignment.query.filter_by(subject_id=id).first():
        flash('No se puede eliminar esta asignatura porque tiene asignaciones de profesores', 'danger')
        return redirect(url_for('admin.subjects'))
    
    # Verificar si hay calificaciones asociadas a esta asignatura
    if StudentGrade.query.join(TeacherAssignment).filter(TeacherAssignment.subject_id == id).first():
        flash('No se puede eliminar esta asignatura porque tiene calificaciones asociadas', 'danger')
        return redirect(url_for('admin.subjects'))
    
    db.session.delete(subject)
    db.session.commit()
    flash('Asignatura eliminada correctamente', 'success')
    return redirect(url_for('admin.subjects'))

# Rutas para gestión de estudiantes
@admin.route('/students')
@login_required
def students():
    students = Student.query.all()
    return render_template('admin/students.html', title='Estudiantes', students=students)

@admin.route('/students/new', methods=['GET', 'POST'])
@login_required
def new_student():
    form = StudentForm()
    form.section_id.choices = [(s.id, f"{s.grade.name}{s.name}") for s in Section.query.join(Grade).order_by(Grade.level, Section.name).all()]
    
    if form.validate_on_submit():
        student = Student(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            student_id=form.student_id.data,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            address=form.address.data,
            phone=form.phone.data,
            email=form.email.data,
            section_id=form.section_id.data,
            is_active=form.is_active.data
        )
        db.session.add(student)
        db.session.commit()
        flash('Estudiante creado correctamente', 'success')
        return redirect(url_for('admin.students'))
        
    return render_template('admin/student_form.html', title='Nuevo Estudiante', form=form)

@admin.route('/students/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    student = Student.query.get_or_404(id)
    form = StudentForm(obj=student)
    form.section_id.choices = [(s.id, f"{s.grade.name}{s.name}") for s in Section.query.join(Grade).order_by(Grade.level, Section.name).all()]
    
    if form.validate_on_submit():
        student.first_name = form.first_name.data
        student.last_name = form.last_name.data
        student.student_id = form.student_id.data
        student.date_of_birth = form.date_of_birth.data
        student.gender = form.gender.data
        student.address = form.address.data
        student.phone = form.phone.data
        student.email = form.email.data
        student.section_id = form.section_id.data
        student.is_active = form.is_active.data
        
        db.session.commit()
        flash('Estudiante actualizado correctamente', 'success')
        return redirect(url_for('admin.students'))
        
    return render_template('admin/student_form.html', title='Editar Estudiante', form=form)

@admin.route('/students/<int:id>/delete', methods=['POST'])
@login_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    
    # Verificar si hay calificaciones asociadas a este estudiante
    if StudentGrade.query.filter_by(student_id=id).first() or FinalGrade.query.filter_by(student_id=id).first():
        flash('No se puede eliminar este estudiante porque tiene calificaciones asociadas', 'danger')
        return redirect(url_for('admin.students'))
    
    db.session.delete(student)
    db.session.commit()
    flash('Estudiante eliminado correctamente', 'success')
    return redirect(url_for('admin.students'))

# Rutas para gestión de profesores
@admin.route('/teachers')
@login_required
def teachers():
    teachers = Teacher.query.all()
    return render_template('admin/teachers.html', title='Gestión de Profesores', teachers=teachers)

@admin.route('/teachers/new', methods=['GET', 'POST'])
@login_required
def new_teacher():
    form = TeacherForm()
    
    if form.validate_on_submit():
        # Crear usuario primero
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role='teacher'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        
        # Crear perfil de profesor
        teacher = Teacher(
            user=user,
            specialization=form.specialization.data,
            qualification=form.qualification.data,
            phone=form.phone.data
        )
        db.session.add(teacher)
        db.session.commit()
        
        flash('Profesor creado correctamente', 'success')
        return redirect(url_for('admin.teachers'))
        
    return render_template('admin/teacher_form.html', title='Nuevo Profesor', form=form)

@admin.route('/teachers/pre-register', methods=['GET', 'POST'])
@login_required
def pre_register_teacher():
    form = TeacherPreRegistrationForm()
    if form.validate_on_submit():
        # Crear usuario sin contraseña
        user = User(
            identification_number=form.identification_number.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role='teacher',
            is_registered=False
        )
        db.session.add(user)
        
        # Crear perfil de profesor
        teacher = Teacher(
            user=user,
            specialization=form.specialization.data
        )
        db.session.add(teacher)
        
        db.session.commit()
        flash(f'Profesor pre-registrado correctamente. Cédula: {form.identification_number.data}', 'success')
        return redirect(url_for('admin.teachers'))
        
    return render_template('admin/teacher_pre_register.html', title='Pre-Registrar Profesor', form=form)

@admin.route('/teachers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_teacher(id):
    teacher = Teacher.query.get_or_404(id)
    form = TeacherPreRegistrationForm()
    
    if form.validate_on_submit():
        # Verificar si la cédula ya está en uso por otro usuario
        existing_user = User.query.filter_by(identification_number=form.identification_number.data).first()
        if existing_user and existing_user.id != teacher.user.id:
            flash('Esta cédula ya está en uso por otro usuario', 'danger')
            return redirect(url_for('admin.edit_teacher', id=id))
            
        # Verificar si el email ya está en uso por otro usuario
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user and existing_user.id != teacher.user.id:
            flash('Este email ya está en uso por otro usuario', 'danger')
            return redirect(url_for('admin.edit_teacher', id=id))
            
        # Actualizar datos
        teacher.user.identification_number = form.identification_number.data
        teacher.user.email = form.email.data
        teacher.user.first_name = form.first_name.data
        teacher.user.last_name = form.last_name.data
        teacher.specialization = form.specialization.data
        
        db.session.commit()
        flash('Profesor actualizado correctamente', 'success')
        return redirect(url_for('admin.teachers'))
        
    # Cargar datos actuales en el formulario
    if request.method == 'GET':
        form.identification_number.data = teacher.user.identification_number
        form.email.data = teacher.user.email
        form.first_name.data = teacher.user.first_name
        form.last_name.data = teacher.user.last_name
        form.specialization.data = teacher.specialization
        
    return render_template('admin/teacher_pre_register.html', title='Editar Profesor', form=form, teacher=teacher)

@admin.route('/teachers/<int:id>/delete', methods=['POST'])
@login_required
def delete_teacher(id):
    teacher = Teacher.query.get_or_404(id)
    
    # No permitir eliminar si tiene asignaciones
    if teacher.assignments.count() > 0:
        flash('No se puede eliminar este profesor porque tiene asignaciones', 'danger')
        return redirect(url_for('admin.teachers'))
        
    # Eliminar usuario (esto también eliminará el perfil de profesor debido a la cascada)
    db.session.delete(teacher.user)
    db.session.commit()
    
    flash('Profesor eliminado correctamente', 'success')
    return redirect(url_for('admin.teachers'))


# Rutas para gestión de asignaciones de profesores
@admin.route('/assignments')
@login_required
def assignments():
    # Obtener el año académico activo
    active_year = AcademicYear.query.filter_by(is_active=True).first()
    
    if not active_year:
        flash('No hay un año académico activo. Por favor, active un año académico primero.', 'warning')
        return redirect(url_for('admin.academic_years'))
    
    assignments = TeacherAssignment.query.filter_by(academic_year_id=active_year.id).all()
    return render_template('admin/assignments.html', title='Asignaciones de Profesores', assignments=assignments, active_year=active_year)

@admin.route('/assignments/new', methods=['GET', 'POST'])
@login_required
def new_assignment():
    form = TeacherAssignmentForm()
    
    # Cargar opciones para los selects
    active_year = AcademicYear.query.filter_by(is_active=True).first()
    if not active_year:
        flash('No hay un año académico activo. Por favor, active un año académico primero.', 'warning')
        return redirect(url_for('admin.academic_years'))
    
    form.teacher_id.choices = [(t.id, f"{t.user.last_name}, {t.user.first_name}") for t in Teacher.query.join(User).order_by(User.last_name).all()]
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.order_by(Subject.name).all()]
    form.section_id.choices = [(s.id, f"{s.grade.name}{s.name}") for s in Section.query.join(Grade).order_by(Grade.level, Section.name).all()]
    
    if form.validate_on_submit():
        # Verificar si ya existe una asignación para esta combinación
        existing = TeacherAssignment.query.filter_by(
            teacher_id=form.teacher_id.data,
            subject_id=form.subject_id.data,
            section_id=form.section_id.data,
            academic_year_id=active_year.id
        ).first()
        
        if existing:
            flash('Ya existe una asignación con estos datos', 'danger')
            return render_template('admin/assignment_form.html', title='Nueva Asignación', form=form)
        
        assignment = TeacherAssignment(
            teacher_id=form.teacher_id.data,
            subject_id=form.subject_id.data,
            section_id=form.section_id.data,
            academic_year_id=active_year.id
        )
        db.session.add(assignment)
        db.session.commit()
        
        flash('Asignación creada correctamente', 'success')
        return redirect(url_for('admin.assignments'))
        
    return render_template('admin/assignment_form.html', title='Nueva Asignación', form=form, active_year=active_year)

@admin.route('/assignments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_assignment(id):
    assignment = TeacherAssignment.query.get_or_404(id)
    form = TeacherAssignmentForm(obj=assignment)
    
    # Cargar opciones para los selects
    form.teacher_id.choices = [(t.id, f"{t.user.last_name}, {t.user.first_name}") for t in Teacher.query.join(User).order_by(User.last_name).all()]
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.order_by(Subject.name).all()]
    form.section_id.choices = [(s.id, f"{s.grade.name}{s.name}") for s in Section.query.join(Grade).order_by(Grade.level, Section.name).all()]
    
    if form.validate_on_submit():
        # Verificar si ya existe una asignación para esta combinación (excluyendo la actual)
        existing = TeacherAssignment.query.filter(
            TeacherAssignment.teacher_id == form.teacher_id.data,
            TeacherAssignment.subject_id == form.subject_id.data,
            TeacherAssignment.section_id == form.section_id.data,
            TeacherAssignment.academic_year_id == assignment.academic_year_id,
            TeacherAssignment.id != id
        ).first()
        
        if existing:
            flash('Ya existe una asignación con estos datos', 'danger')
            return render_template('admin/assignment_form.html', title='Editar Asignación', form=form)
        
        assignment.teacher_id = form.teacher_id.data
        assignment.subject_id = form.subject_id.data
        assignment.section_id = form.section_id.data
        
        db.session.commit()
        flash('Asignación actualizada correctamente', 'success')
        return redirect(url_for('admin.assignments'))
        
    return render_template('admin/assignment_form.html', title='Editar Asignación', form=form, active_year=assignment.academic_year)

@admin.route('/assignments/<int:id>/delete', methods=['POST'])
@login_required
def delete_assignment(id):
    assignment = TeacherAssignment.query.get_or_404(id)
    
    # Verificar si hay calificaciones asociadas a esta asignación
    if StudentGrade.query.filter_by(assignment_id=id).first() or FinalGrade.query.filter_by(assignment_id=id).first():
        flash('No se puede eliminar esta asignación porque tiene calificaciones asociadas', 'danger')
        return redirect(url_for('admin.assignments'))
    
    db.session.delete(assignment)
    db.session.commit()
    flash('Asignación eliminada correctamente', 'success')
    return redirect(url_for('admin.assignments'))

# Rutas para gestión de tipos de calificación
@admin.route('/grade-types')
@login_required
def grade_types():
    grade_types = GradeType.query.all()
    return render_template('admin/grade_types.html', title='Tipos de Calificación', grade_types=grade_types)

@admin.route('/grade-types/new', methods=['GET', 'POST'])
@login_required
def new_grade_type():
    form = GradeTypeForm()
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.order_by(Subject.name).all()]
    
    if form.validate_on_submit():
        # Verificar que los pesos no excedan 100%
        existing_weight = db.session.query(db.func.sum(GradeType.weight)).filter_by(subject_id=form.subject_id.data).scalar() or 0
        if existing_weight + form.weight.data > 100:
            flash(f'El peso total de los tipos de calificación para esta asignatura excedería el 100% (actual: {existing_weight}%)', 'danger')
            return render_template('admin/grade_type_form.html', title='Nuevo Tipo de Calificación', form=form)
        
        grade_type = GradeType(
            name=form.name.data,
            description=form.description.data,
            weight=form.weight.data,
            subject_id=form.subject_id.data
        )
        db.session.add(grade_type)
        db.session.commit()
        flash('Tipo de calificación creado correctamente', 'success')
        return redirect(url_for('admin.grade_types'))
        
    return render_template('admin/grade_type_form.html', title='Nuevo Tipo de Calificación', form=form)

@admin.route('/grade-types/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_grade_type(id):
    grade_type = GradeType.query.get_or_404(id)
    form = GradeTypeForm(obj=grade_type)
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.order_by(Subject.name).all()]
    
    if form.validate_on_submit():
        # Verificar que los pesos no excedan 100%
        existing_weight = db.session.query(db.func.sum(GradeType.weight)).filter(
            GradeType.subject_id == form.subject_id.data,
            GradeType.id != id
        ).scalar() or 0
        
        if existing_weight + form.weight.data > 100:
            flash(f'El peso total de los tipos de calificación para esta asignatura excedería el 100% (actual: {existing_weight}%)', 'danger')
            return render_template('admin/grade_type_form.html', title='Editar Tipo de Calificación', form=form)
        
        grade_type.name = form.name.data
        grade_type.description = form.description.data
        grade_type.weight = form.weight.data
        grade_type.subject_id = form.subject_id.data
        
        db.session.commit()
        flash('Tipo de calificación actualizado correctamente', 'success')
        return redirect(url_for('admin.grade_types'))
        
    return render_template('admin/grade_type_form.html', title='Editar Tipo de Calificación', form=form)

@admin.route('/grade-types/<int:id>/delete', methods=['POST'])
@login_required
def delete_grade_type(id):
    grade_type = GradeType.query.get_or_404(id)
    
    # Verificar si hay calificaciones asociadas a este tipo
    if StudentGrade.query.filter_by(grade_type_id=id).first():
        flash('No se puede eliminar este tipo de calificación porque tiene calificaciones asociadas', 'danger')
        return redirect(url_for('admin.grade_types'))
    
    db.session.delete(grade_type)
    db.session.commit()
    flash('Tipo de calificación eliminado correctamente', 'success')
    return redirect(url_for('admin.grade_types'))

# Ruta para activar/desactivar año académico
@admin.route('/academic-years/<int:id>/toggle-active', methods=['POST'])
@login_required
def toggle_academic_year(id):
    year = AcademicYear.query.get_or_404(id)
    
    if year.is_active:
        year.is_active = False
        message = f'Año académico {year.name} desactivado correctamente'
    else:
        # Desactivar todos los demás años
        AcademicYear.query.update({AcademicYear.is_active: False})
        year.is_active = True
        message = f'Año académico {year.name} activado correctamente'
    
    db.session.commit()
    flash(message, 'success')
    return redirect(url_for('admin.academic_years'))

# Ruta para editar año académico
@admin.route('/academic-years/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_academic_year(id):
    year = AcademicYear.query.get_or_404(id)
    form = AcademicYearForm(obj=year)
    
    if form.validate_on_submit():
        year.name = form.name.data
        year.start_date = form.start_date.data
        year.end_date = form.end_date.data
        
        # Si se marca como activo, desactivar los demás
        if form.is_active.data and not year.is_active:
            AcademicYear.query.update({AcademicYear.is_active: False})
            year.is_active = True
        elif not form.is_active.data and year.is_active:
            year.is_active = False
        
        db.session.commit()
        flash('Año académico actualizado correctamente', 'success')
        return redirect(url_for('admin.academic_years'))
        
    return render_template('admin/academic_year_form.html', title='Editar Año Académico', form=form)

@admin.route('/academic-years/<int:id>/delete', methods=['POST'])
@login_required
def delete_academic_year(id):
    year = AcademicYear.query.get_or_404(id)
    
    # Verificar si hay períodos asociados
    if Period.query.filter_by(academic_year_id=id).first():
        flash('No se puede eliminar este año académico porque tiene períodos asociados', 'danger')
        return redirect(url_for('admin.academic_years'))
    
    # Verificar si hay asignaciones asociadas
    if TeacherAssignment.query.filter_by(academic_year_id=id).first():
        flash('No se puede eliminar este año académico porque tiene asignaciones de profesores asociadas', 'danger')
        return redirect(url_for('admin.academic_years'))
    
    # No permitir eliminar el año activo
    if year.is_active:
        flash('No se puede eliminar el año académico activo', 'danger')
        return redirect(url_for('admin.academic_years'))
    
    db.session.delete(year)
    db.session.commit()
    flash('Año académico eliminado correctamente', 'success')
    return redirect(url_for('admin.academic_years'))

# Rutas para importación y exportación de datos
@admin.route('/import-export')
@login_required
def import_export():
    return render_template('admin/import_export.html', title='Importación y Exportación de Datos')

@admin.route('/import-students', methods=['GET', 'POST'])
@login_required
def import_students():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        
        if file and file.filename.endswith('.xlsx'):
            try:
                # Procesar archivo Excel
                df = pd.read_excel(file)
                section_id = request.form.get('section_id', type=int)
                section = Section.query.get_or_404(section_id)
                
                # Validar columnas requeridas
                required_columns = ['first_name', 'last_name', 'student_id', 'date_of_birth', 'gender']
                if not all(col in df.columns for col in required_columns):
                    flash('El archivo no tiene el formato correcto. Faltan columnas requeridas.', 'danger')
                    return redirect(request.url)
                
                # Importar estudiantes
                count = 0
                for _, row in df.iterrows():
                    # Verificar si ya existe un estudiante con ese ID
                    existing = Student.query.filter_by(student_id=row['student_id']).first()
                    if existing:
                        continue
                    
                    student = Student(
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        student_id=row['student_id'],
                        date_of_birth=row['date_of_birth'],
                        gender=row['gender'],
                        section_id=section_id,
                        is_active=True
                    )
                    
                    # Campos opcionales
                    if 'address' in df.columns and not pd.isna(row['address']):
                        student.address = row['address']
                    if 'phone' in df.columns and not pd.isna(row['phone']):
                        student.phone = row['phone']
                    if 'email' in df.columns and not pd.isna(row['email']):
                        student.email = row['email']
                    
                    db.session.add(student)
                    count += 1
                
                db.session.commit()
                flash(f'Se importaron {count} estudiantes correctamente', 'success')
                return redirect(url_for('admin.students'))
                
            except Exception as e:
                flash(f'Error al procesar el archivo: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('Formato de archivo no permitido. Use archivos Excel (.xlsx)', 'danger')
            return redirect(request.url)
    
    # Obtener secciones para el formulario
    sections = Section.query.join(Grade).order_by(Grade.level, Section.name).all()
    return render_template('admin/import_students.html', title='Importar Estudiantes', sections=sections)

@admin.route('/export-students/<int:section_id>')
@login_required
def export_students(section_id):
    section = Section.query.get_or_404(section_id)
    students = Student.query.filter_by(section_id=section_id).order_by(Student.last_name, Student.first_name).all()
    
    # Crear DataFrame
    data = []
    for student in students:
        data.append({
            'student_id': student.student_id,
            'first_name': student.first_name,
            'last_name': student.last_name,
            'date_of_birth': student.date_of_birth,
            'gender': student.gender,
            'address': student.address,
            'phone': student.phone,
            'email': student.email
        })
    
    df = pd.DataFrame(data)
    
    # Crear archivo Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Estudiantes')
    
    output.seek(0)
    
    # Enviar archivo como respuesta
    return send_file(
        output,
        as_attachment=True,
        download_name=f'estudiantes_{section.grade.name}{section.name}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# Ruta para configuración del sistema
@admin.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()
    
    # Cargar configuración actual
    if request.method == 'GET':
        # Aquí cargaríamos los valores de la configuración
        pass
    
    if form.validate_on_submit():
        # Guardar configuración
        flash('Configuración actualizada correctamente', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/settings.html', title='Configuración del Sistema', form=form)

# Ruta para ver estadísticas
@admin.route('/statistics')
@login_required
def statistics():
    # Obtener año académico activo
    active_year = AcademicYear.query.filter_by(is_active=True).first()
    if not active_year:
        flash('No hay un año académico activo', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    # Estadísticas generales
    stats = {
        'students_count': Student.query.filter_by(is_active=True).count(),
        'teachers_count': Teacher.query.count(),
        'subjects_count': Subject.query.count(),
        'sections_count': Section.query.count()
    }
    
    # Estadísticas de calificaciones por período
    periods = Period.query.filter_by(academic_year_id=active_year.id).all()
    period_stats = []
    
    for period in periods:
        # Promedio general por período
        avg_grade = db.session.query(db.func.avg(FinalGrade.value)).filter_by(period_id=period.id).scalar() or 0
        
        # Cantidad de aprobados y reprobados
        passing_grade = 70  # Nota de aprobación (ajustar según necesidad)
        passing_count = FinalGrade.query.filter(FinalGrade.period_id == period.id, FinalGrade.value >= passing_grade).count()
        failing_count = FinalGrade.query.filter(FinalGrade.period_id == period.id, FinalGrade.value < passing_grade).count()
        
        period_stats.append({
            'period': period,
            'avg_grade': round(avg_grade, 2),
            'passing_count': passing_count,
            'failing_count': failing_count
        })
    
    return render_template(
        'admin/statistics.html', 
        title='Estadísticas', 
        stats=stats, 
        period_stats=period_stats,
        active_year=active_year
    )
