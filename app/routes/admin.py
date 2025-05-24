from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, jsonify, current_app
from io import BytesIO
import pandas as pd
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from datetime import datetime 
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
    
    print(users)

    return render_template('admin/users.html', title='Gestión de Usuarios', users=users)

@admin.route('/users/new', methods=['GET', 'POST'])
@login_required
def new_user():
    if request.method == 'POST':
        # Obtener datos del formulario
        identification_number = request.form.get('identification_number')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        specialization = request.form.get('specialization')

        # Imprimir los valores para depuración
        # print(f"identification_number: {identification_number}")
        # print(f"email: {email}")
        # print(f"first_name: {first_name}")
        # print(f"last_name: {last_name}")
        # print(f"role: {role}")
        # print(f"password: {'*****' if password else None}")  # No mostrar la contraseña real
        # print(f"specialization: {specialization}")
        
        # Validaciones básicas
        if not identification_number or not email or not first_name or not last_name or not role or not password:
            flash('Todos los campos son requeridos', 'danger')
            return redirect(url_for('admin.users'))
            
        if password != password2:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('admin.users'))
            
        # Verificar si el usuario ya existe
        if User.query.filter_by(identification_number=identification_number).first():
            flash('Esta cédula ya está registrada', 'danger')
            return redirect(url_for('admin.users'))
            
        if User.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'danger')
            return redirect(url_for('admin.users'))
        
        # Crear el usuario
        user = User(
            identification_number=identification_number,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_registered=True  # Como lo crea un admin, se considera registrado
        )
        user.set_password(password)
        db.session.add(user)
        
        # Si es profesor, crear perfil de profesor
        if role == 'teacher':
            teacher = Teacher(
                user=user, 
                specialization=specialization,
                identification_number=identification_number
            )
            db.session.add(teacher)
            
        db.session.commit()
        flash('Usuario creado correctamente', 'success')
        return redirect(url_for('admin.users'))


    
    # Si es GET, mostrar el formulario en un modal
    # Como ahora usamos modales, simplemente redirigimos a la página de usuarios
    return redirect(url_for('admin.users'))

@admin.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        # Obtener datos del formulario
        identification_number = request.form.get('identification_number')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        specialization = request.form.get('specialization')
        
        # Validaciones básicas
        if not identification_number or not email or not first_name or not last_name or not role:
            flash('Todos los campos son requeridos excepto la contraseña', 'danger')
            return redirect(url_for('admin.users'))
            
        if password and password != password2:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('admin.users'))
            
        # Verificar si el usuario ya existe
        existing_user = User.query.filter_by(identification_number=identification_number).first()
        if existing_user and existing_user.id != user.id:
            flash('Esta cédula ya está registrada', 'danger')
            return redirect(url_for('admin.users'))
            
        existing_email = User.query.filter_by(email=email).first()
        if existing_email and existing_email.id != user.id:
            flash('El email ya está registrado', 'danger')
            return redirect(url_for('admin.users'))
        
        # No permitir cambiar el rol si es el único administrador
        if user.is_admin() and User.query.filter_by(role='admin').count() == 1 and role != 'admin':
            flash('No se puede cambiar el rol del único administrador', 'danger')
            return redirect(url_for('admin.users'))
        
        # Actualizar el usuario
        user.identification_number = identification_number
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        
        # Solo cambiar el rol si no es el único administrador
        if not (user.is_admin() and User.query.filter_by(role='admin').count() == 1):
            user.role = role
        
        if password:
            user.set_password(password)
            
        # Actualizar o crear perfil de profesor
        if role == 'teacher':
            if user.teacher_profile:
                user.teacher_profile.specialization = specialization
                user.teacher_profile.identification_number = identification_number
            else:
                teacher = Teacher(
                    user=user, 
                    specialization=specialization,
                    identification_number=identification_number
                )
                db.session.add(teacher)
                
        db.session.commit()
        flash('Usuario actualizado correctamente', 'success')
        return redirect(url_for('admin.users'))
    
    # Si es GET, mostrar el formulario en un modal
    # Como ahora usamos modales, simplemente redirigimos a la página de usuarios
    return redirect(url_for('admin.users'))

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

@admin.route('/users/<int:id>/resend-invitation', methods=['POST'])
@login_required
def resend_invitation(id):
    user = User.query.get_or_404(id)
    
    if user.is_registered:
        flash('Este usuario ya ha completado su registro', 'warning')
        return redirect(url_for('admin.users'))
    
    # Aquí iría la lógica para enviar el correo electrónico
    # Por ahora solo mostramos un mensaje de éxito
    
    flash(f'Se ha reenviado la invitación a {user.email}', 'success')
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

# Rutas para gestión de grados y secciones
@admin.route('/grades')
@login_required
def grades():
    grades = Grade.query.all()
    return render_template('admin/grades.html', title='Grados y Secciones', grades=grades)

# Ruta para obtener secciones de un grado
@admin.route('/grades/<int:id>/sections', methods=['GET'])
@login_required
def get_grade_sections(id):
    grade = Grade.query.get_or_404(id)
    sections = [{'id': s.id, 'name': s.name} for s in grade.sections]
    return jsonify({'sections': sections})

# Ruta para obtener detalles de un grado por AJAX
@admin.route('/grades/<int:id>/details', methods=['GET'])
@login_required
def get_grade_details(id):
    grade = Grade.query.get_or_404(id)
    sections = [{'id': s.id, 'name': s.name} for s in grade.sections]
    
    return jsonify({
        'id': grade.id,
        'name': grade.name,
        'level': grade.level,
        'sections': sections
    })

# Ruta para crear un grado por AJAX
@admin.route('/grades/create', methods=['POST'])
@login_required
def create_grade_ajax():
    try:
        name = request.form.get('name')
        level = request.form.get('level')
        sections = request.form.getlist('sections[]')
        
        if not name or not level:
            return jsonify({'success': False, 'message': 'Nombre y nivel son requeridos'}), 400
            
        grade = Grade(name=name, level=level)
        db.session.add(grade)
        db.session.flush()  # Para obtener el ID del grado antes de crear las secciones
        
        # Si no se especificaron secciones, crear una sección predeterminada "U"
        if not sections:
            sections = ["U"]
            
        # Crear secciones para el grado
        for section_name in sections:
            if section_name.strip():  # Ignorar secciones vacías
                section = Section(name=section_name.strip(), grade_id=grade.id)
                db.session.add(section)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Grado creado correctamente con sus secciones',
            'grade': {
                'id': grade.id,
                'name': grade.name,
                'level': grade.level,
                'sections_count': len(sections)
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Ruta para actualizar un grado por AJAX
@admin.route('/grades/<int:id>/update', methods=['POST'])
@login_required
def update_grade_ajax(id):
    try:
        grade = Grade.query.get_or_404(id)
        
        name = request.form.get('name')
        level = request.form.get('level')
        
        if not name or not level:
            return jsonify({'success': False, 'message': 'Nombre y nivel son requeridos'}), 400
            
        grade.name = name
        grade.level = level
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Grado actualizado correctamente',
            'grade': {
                'id': grade.id,
                'name': grade.name,
                'level': grade.level
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Ruta para eliminar un grado por AJAX
@admin.route('/grades/<int:id>/delete', methods=['POST'])
@login_required
def delete_grade_ajax(id):
    try:
        grade = Grade.query.get_or_404(id)
        
        # Verificar si tiene secciones con estudiantes
        for section in grade.sections:
            if section.students.count() > 0:
                return jsonify({
                    'success': False, 
                    'message': f'No se puede eliminar el grado porque la sección {section.name} tiene estudiantes asociados'
                }), 400
            
        db.session.delete(grade)  # Esto eliminará también las secciones (cascade)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Grado eliminado correctamente con todas sus secciones'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Rutas para gestión de secciones
@admin.route('/sections')
@login_required
def sections():
    # Obtener el parámetro grade_id si existe
    grade_id = request.args.get('grade_id', type=int)
    
    # Filtrar secciones por grado si se proporciona grade_id
    if grade_id:
        grade = Grade.query.get_or_404(grade_id)
        sections = Section.query.filter_by(grade_id=grade_id).all()
        return render_template('admin/sections.html', title='Secciones', sections=sections, grade=grade)
    
    # Si no hay grade_id, mostrar todas las secciones
    sections = Section.query.all()
    grades = Grade.query.all()
    return render_template('admin/sections.html', title='Secciones', sections=sections, grades=grades)

# Ruta para crear una sección por AJAX
@admin.route('/sections/create', methods=['POST'])
@login_required
def create_section_ajax():
    try:
        name = request.form.get('name')
        grade_id = request.form.get('grade_id')
        
        if not name or not grade_id:
            return jsonify({'success': False, 'message': 'Nombre y grado son requeridos'}), 400
            
        # Verificar que el grado existe
        grade = Grade.query.get_or_404(grade_id)
        
        # Verificar que no exista una sección con el mismo nombre en el mismo grado
        existing_section = Section.query.filter_by(name=name, grade_id=grade_id).first()
        if existing_section:
            return jsonify({'success': False, 'message': f'Ya existe una sección {name} en este grado'}), 400
            
        section = Section(name=name, grade_id=grade_id)
        db.session.add(section)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Sección creada correctamente',
            'section': {
                'id': section.id,
                'name': section.name,
                'grade_id': section.grade_id
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Ruta para actualizar una sección por AJAX
@admin.route('/sections/<int:id>/update', methods=['POST'])
@login_required
def update_section_ajax(id):
    try:
        section = Section.query.get_or_404(id)
        
        name = request.form.get('name')
        
        if not name:
            return jsonify({'success': False, 'message': 'Nombre es requerido'}), 400
            
        # Verificar que no exista otra sección con el mismo nombre en el mismo grado
        existing_section = Section.query.filter_by(name=name, grade_id=section.grade_id).first()
        if existing_section and existing_section.id != section.id:
            return jsonify({'success': False, 'message': f'Ya existe una sección {name} en este grado'}), 400
            
        section.name = name
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Sección actualizada correctamente',
            'section': {
                'id': section.id,
                'name': section.name
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin.route('/sections/<int:id>/delete', methods=['POST'])
@login_required
def delete_section_ajax(id):
    try:
        section = Section.query.get_or_404(id)
        
        # Verificar si tiene estudiantes
        if section.students.count() > 0:
            return jsonify({
                'success': False, 
                'message': f'No se puede eliminar la sección porque tiene {section.students.count()} estudiantes asociados'
            }), 400
            
        # Verificar que no sea la única sección del grado
        if section.grade.sections.count() == 1:
            return jsonify({
                'success': False, 
                'message': 'No se puede eliminar la única sección del grado'
            }), 400
            
        db.session.delete(section)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Sección eliminada correctamente'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Rutas para gestión de asignaturas
@admin.route('/subjects')
@login_required
def subjects():
    subjects = Subject.query.all()
    grades = Grade.query.all()
    
    # Obtener las asignaciones para cada asignatura
    for subject in subjects:
        # Asegurarse de que las relaciones estén cargadas
        subject.teacher_assignments.all()
    
    return render_template('admin/subjects.html', title='Asignaturas', subjects=subjects, grades=grades)

@admin.route('/subjects/new', methods=['POST'])
@login_required
def new_subject():
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        
        # Validar que todos los campos estén presentes
        if not all([name, code]):
            flash('Todos los campos son requeridos', 'danger')
            return redirect(url_for('admin.subjects'))
            
        # Verificar si ya existe una asignatura con el mismo código
        existing = Subject.query.filter_by(code=code).first()
        if existing:
            flash(f'Ya existe una asignatura con el código {code}', 'danger')
            return redirect(url_for('admin.subjects'))
            
        # Crear nueva asignatura
        subject = Subject(name=name, code=code)
        db.session.add(subject)
        db.session.commit()
        
        flash('Asignatura creada correctamente', 'success')
        return redirect(url_for('admin.subjects'))
        
    return redirect(url_for('admin.subjects'))

@admin.route('/subjects/<int:id>/edit', methods=['POST'])
@login_required
def edit_subject(id):
    subject = Subject.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        
        # Validar que todos los campos estén presentes
        if not all([name, code]):
            flash('Todos los campos son requeridos', 'danger')
            return redirect(url_for('admin.subjects'))
            
        # Verificar si ya existe otra asignatura con el mismo código
        existing = Subject.query.filter(Subject.id != id, Subject.code == code).first()
        if existing:
            flash(f'Ya existe otra asignatura con el código {code}', 'danger')
            return redirect(url_for('admin.subjects'))
            
        # Actualizar asignatura
        subject.name = name
        subject.code = code
        db.session.commit()
        
        flash('Asignatura actualizada correctamente', 'success')
        return redirect(url_for('admin.subjects'))
        
    return redirect(url_for('admin.subjects'))

@admin.route('/subjects/<int:id>/delete', methods=['POST'])
@login_required
def delete_subject(id):
    subject = Subject.query.get_or_404(id)
    
    # Verificar si hay asignaciones de profesores a esta asignatura
    if TeacherAssignment.query.filter_by(subject_id=id).first():
        flash('No se puede eliminar esta asignatura porque tiene asignaciones de profesores', 'danger')
        return redirect(url_for('admin.subjects'))
    
    # Verificar si hay calificaciones asociadas a esta asignatura
    if StudentGrade.query.filter_by(subject_id=id).first():
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
    # Obtener parámetros de filtrado
    grade_id = request.args.get('grade_id', type=int)
    section_id = request.args.get('section_id', type=int)
    search = request.args.get('search', '')
    
    # Consulta base
    query = Student.query
    
    # Aplicar filtros
    if grade_id:
        sections = Section.query.filter_by(grade_id=grade_id).all()
        section_ids = [section.id for section in sections]
        query = query.filter(Student.section_id.in_(section_ids))
    
    if section_id:
        query = query.filter_by(section_id=section_id)
    
    if search:
        query = query.filter(
            db.or_(
                Student.first_name.ilike(f'%{search}%'),
                Student.last_name.ilike(f'%{search}%'),
                Student.student_id.ilike(f'%{search}%')
            )
        )
    
    # Ordenar y paginar
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Student.last_name, Student.first_name).paginate(
        page=page, per_page=20, error_out=False
    )
    students = pagination.items
    
    # Obtener grados y secciones para los filtros
    grades = Grade.query.all()
    sections = Section.query.filter_by(grade_id=grade_id).all() if grade_id else []
    
    # Obtener año académico activo y asignaturas
    active_year = AcademicYear.query.filter_by(is_active=True).first()
    subjects = Subject.query.all()
    
    # Crear formulario para nuevo estudiante
    form = StudentForm()
    form.section_id.choices = [(s.id, f"{s.grade.name} '{s.name}'") for s in Section.query.join(Grade).all()]
    
    # Configuración
    passing_grade = 70  # Nota de aprobación (esto podría venir de la configuración)
    
    return render_template(
        'admin/students.html', 
        title='Estudiantes', 
        students=students,
        pagination=pagination,
        grades=grades,
        sections=sections,
        active_year=active_year,
        subjects=subjects,
        form=form,
        passing_grade=passing_grade,
        now=datetime.now()
    )

# Ruta para crear un nuevo estudiante
@admin.route('/students/new', methods=['POST'])
@login_required
def new_student():
    form = StudentForm()
    form.section_id.choices = [(s.id, f"{s.grade.name} '{s.name}'") for s in Section.query.join(Grade).all()]
    
    if form.validate_on_submit():
        student = Student(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            student_id=form.student_id.data,
            birth_date=form.birth_date.data,
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
    
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('admin.students'))

# Ruta para editar un estudiante
@admin.route('/students/<int:id>/edit', methods=['POST'])
@login_required
def edit_student(id):
    student = Student.query.get_or_404(id)
    form = StudentForm()
    form.section_id.choices = [(s.id, f"{s.grade.name} '{s.name}'") for s in Section.query.join(Grade).all()]
    
    # Guardar el ID de la base de datos para validación
    form.student_id_db = student.id
    
    if form.validate_on_submit():
        student.first_name = form.first_name.data
        student.last_name = form.last_name.data
        student.student_id = form.student_id.data
        student.birth_date = form.birth_date.data
        student.gender = form.gender.data
        student.address = form.address.data
        student.phone = form.phone.data
        student.email = form.email.data
        student.section_id = form.section_id.data
        student.is_active = form.is_active.data
        
        db.session.commit()
        flash('Estudiante actualizado correctamente', 'success')
        return redirect(url_for('admin.students'))
    
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('admin.students'))

# Ruta para eliminar un estudiante
@admin.route('/students/<int:id>/delete', methods=['POST'])
@login_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash('Estudiante eliminado correctamente', 'success')
    return redirect(url_for('admin.students'))

# Ruta para obtener detalles de un estudiante (para el modal de ver)
@admin.route('/students/<int:id>/details', methods=['GET'])
@login_required
def get_student_details(id):
    student = Student.query.get_or_404(id)
    return render_template('admin/partials/student_details.html', student=student)

# Ruta para obtener el formulario de edición de un estudiante
@admin.route('/students/<int:id>/edit-form', methods=['GET'])
@login_required
def get_student_edit_form(id):
    student = Student.query.get_or_404(id)
    form = StudentForm(obj=student)
    form.section_id.choices = [(s.id, f"{s.grade.name} '{s.name}'") for s in Section.query.join(Grade).all()]
    return render_template('admin/partials/student_edit_form.html', form=form, student=student)

# Ruta para obtener el formulario de confirmación de eliminación
@admin.route('/students/<int:id>/delete-form', methods=['GET'])
@login_required
def get_student_delete_form(id):
    student = Student.query.get_or_404(id)
    return render_template('admin/partials/student_delete_form.html', student=student)

# Ruta para editar un estudiante (versión AJAX)
@admin.route('/students/<int:id>/edit-ajax', methods=['POST'])
@login_required
def edit_student_ajax(id):
    student = Student.query.get_or_404(id)
    form = StudentForm()
    form.section_id.choices = [(s.id, f"{s.grade.name} '{s.name}'") for s in Section.query.join(Grade).all()]
    
    if form.validate_on_submit():
        student.first_name = form.first_name.data
        student.last_name = form.last_name.data
        student.student_id = form.student_id.data
        student.birth_date = form.birth_date.data
        student.gender = form.gender.data
        student.address = form.address.data
        student.phone = form.phone.data
        student.email = form.email.data
        student.section_id = form.section_id.data
        student.is_active = form.is_active.data
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Estudiante actualizado correctamente'})
    
    errors = []
    for field, field_errors in form.errors.items():
        for error in field_errors:
            errors.append(f"{getattr(form, field).label.text}: {error}")
    
    return jsonify({'success': False, 'message': 'Error en el formulario', 'errors': errors})

# Ruta para eliminar un estudiante (versión AJAX)
@admin.route('/students/<int:id>/delete-ajax', methods=['POST'])
@login_required
def delete_student_ajax(id):
    student = Student.query.get_or_404(id)
    
    try:
        db.session.delete(student)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Estudiante eliminado correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al eliminar el estudiante: {str(e)}'})

# Ruta para importar estudiantes desde Excel
@admin.route('/students/import', methods=['POST'])
@login_required
def import_students():
    if 'file' not in request.files:
        flash('No se ha seleccionado ningún archivo', 'danger')
        return redirect(url_for('admin.students'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No se ha seleccionado ningún archivo', 'danger')
        return redirect(url_for('admin.students'))
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('El archivo debe ser de tipo Excel (.xlsx, .xls)', 'danger')
        return redirect(url_for('admin.students'))
    
    section_id = request.form.get('section_id', type=int)
    if not section_id:
        flash('Debe seleccionar una sección', 'danger')
        return redirect(url_for('admin.students'))
    
    is_active = 'is_active' in request.form
    
    try:
        # Leer archivo Excel
        df = pd.read_excel(file)
        
        # Validar columnas requeridas
        required_columns = ['Cédula', 'Nombre', 'Apellido']
        for col in required_columns:
            if col not in df.columns:
                flash(f'El archivo no contiene la columna requerida: {col}', 'danger')
                return redirect(url_for('admin.students'))
        
        # Procesar datos
        count = 0
        errors = 0
        for _, row in df.iterrows():
            try:
                # Verificar si ya existe un estudiante con esa cédula
                existing = Student.query.filter_by(student_id=str(row['Cédula'])).first()
                if existing:
                    flash(f'Ya existe un estudiante con la cédula {row["Cédula"]}', 'warning')
                    errors += 1
                    continue
                
                # Crear nuevo estudiante
                student = Student(
                    first_name=row['Nombre'],
                    last_name=row['Apellido'],
                    student_id=str(row['Cédula']),
                    section_id=section_id,
                    is_active=is_active
                )
                
                # Campos opcionales
                if 'Fecha de Nacimiento' in df.columns and not pd.isna(row['Fecha de Nacimiento']):
                    if isinstance(row['Fecha de Nacimiento'], str):
                        student.birth_date = datetime.strptime(row['Fecha de Nacimiento'], '%d/%m/%Y').date()
                    else:
                        student.birth_date = row['Fecha de Nacimiento']
                
                if 'Género' in df.columns and not pd.isna(row['Género']):
                    student.gender = row['Género']
                
                if 'Dirección' in df.columns and not pd.isna(row['Dirección']):
                    student.address = row['Dirección']
                
                if 'Teléfono' in df.columns and not pd.isna(row['Teléfono']):
                    student.phone = str(row['Teléfono'])
                
                if 'Email' in df.columns and not pd.isna(row['Email']):
                    student.email = row['Email']
                
                db.session.add(student)
                count += 1
            except Exception as e:
                errors += 1
                flash(f'Error al procesar la fila {_+2}: {str(e)}', 'danger')
        
        db.session.commit()
        flash(f'Se importaron {count} estudiantes correctamente. Errores: {errors}', 'success')
    except Exception as e:
        flash(f'Error al procesar el archivo: {str(e)}', 'danger')
    
    return redirect(url_for('admin.students'))

# Ruta para descargar plantilla de importación
@admin.route('/students/download-template')
@login_required
def download_student_template():
    # Crear DataFrame con las columnas de ejemplo
    data = {
        'Cédula': ['12345678', '87654321'],
        'Nombre': ['Juan', 'María'],
        'Apellido': ['Pérez', 'González'],
        'Fecha de Nacimiento': ['01/01/2010', '15/05/2009'],
        'Género': ['M', 'F'],
        'Dirección': ['Calle Principal #123', 'Avenida Central #456'],
        'Teléfono': ['555-1234', '555-5678'],
        'Email': ['juan@example.com', 'maria@example.com']
    }
    df = pd.DataFrame(data)
    
    # Crear archivo Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Estudiantes')
        
        # Ajustar ancho de columnas
        worksheet = writer.sheets['Estudiantes']
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='plantilla_estudiantes.xlsx'
    )

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

@admin.route('/users/pre-register-teacher', methods=['POST'])
@login_required
def pre_register_teacher():
    if request.method == 'POST':
        identification_number = request.form.get('identification_number')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        specialization = request.form.get('specialization')
        
        # Validaciones básicas
        if not identification_number or not email or not first_name or not last_name:
            flash('Todos los campos son requeridos excepto la especialización', 'danger')
            return redirect(url_for('admin.users'))
            
        # Verificar si el usuario ya existe
        if User.query.filter_by(identification_number=identification_number).first():
            flash('Esta cédula ya está registrada', 'danger')
            return redirect(url_for('admin.users'))
            
        if User.query.filter_by(email=email).first():
            flash('Este email ya está registrado', 'danger')
            return redirect(url_for('admin.users'))
        
        # Crear el usuario pre-registrado
        user = User(
            identification_number=identification_number,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role='teacher',
            is_registered=False  # No está registrado hasta que complete su registro
        )
        db.session.add(user)
        
        # Crear perfil de profesor
        teacher = Teacher(
            user=user, 
            specialization=specialization,
            identification_number=identification_number,
            is_registered=False
        )
        db.session.add(teacher)
            
        db.session.commit()
        
        # Aquí iría el código para enviar un email de invitación
        
        flash('Profesor pre-registrado correctamente. Se ha enviado un email con instrucciones para completar el registro.', 'success')
        return redirect(url_for('admin.users'))
        
    # Si es GET, redirigir a la página de usuarios
    return redirect(url_for('admin.users'))
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
    # Obtener parámetros de filtrado
    academic_year_id = request.args.get('academic_year', type=int)
    teacher_id = request.args.get('teacher', type=int)
    subject_id = request.args.get('subject', type=int)
    section_id = request.args.get('section', type=int)
    
    # Consulta base para asignaciones
    query = TeacherAssignment.query
    
    # Aplicar filtros si se proporcionan
    if academic_year_id:
        query = query.filter_by(academic_year_id=academic_year_id)
    if teacher_id:
        query = query.filter_by(teacher_id=teacher_id)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    if section_id:
        query = query.filter_by(section_id=section_id)
    
    # Ordenar por año académico, profesor, asignatura y sección
    query = query.order_by(
        TeacherAssignment.academic_year_id.desc(),
        TeacherAssignment.teacher_id,
        TeacherAssignment.subject_id,
        TeacherAssignment.section_id
    )
    
    # Paginar resultados
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    assignments = pagination.items
    
    # Obtener datos para los selectores de filtro
    academic_years = AcademicYear.query.order_by(AcademicYear.start_date.desc()).all()
    teachers = Teacher.query.join(User).order_by(User.last_name, User.first_name).all()
    subjects = Subject.query.order_by(Subject.name).all()
    
    # Obtener todas las secciones con sus grados para mostrar en el filtro
    sections = Section.query.join(Grade).order_by(Grade.level, Grade.name, Section.name).all()
    
    # Obtener todos los grados para el modal de nueva asignación
    grades = Grade.query.order_by(Grade.level, Grade.name).all()
    
    return render_template(
        'admin/assignments.html',
        title='Asignaciones de Profesores',
        assignments=assignments,
        pagination=pagination,
        academic_years=academic_years,
        teachers=teachers,
        subjects=subjects,
        sections=sections,
        grades=grades,
        request=request
    )

@admin.route('/assignments/new', methods=['POST'])
@login_required
def new_assignment():
    if request.method == 'POST':
        teacher_id = request.form.get('teacher_id', type=int)
        subject_id = request.form.get('subject_id', type=int)
        section_id = request.form.get('section_id', type=int)
        academic_year_id = request.form.get('academic_year_id', type=int)
        
        # Validar que todos los campos estén presentes
        if not all([teacher_id, subject_id, section_id, academic_year_id]):
            flash('Todos los campos son requeridos', 'danger')
            return redirect(url_for('admin.assignments'))
        
        # Verificar si ya existe una asignación igual
        existing = TeacherAssignment.query.filter_by(
            teacher_id=teacher_id,
            subject_id=subject_id,
            section_id=section_id,
            academic_year_id=academic_year_id
        ).first()
        
        if existing:
            flash('Ya existe una asignación con estos datos', 'danger')
            return redirect(url_for('admin.assignments'))
        
        # Crear nueva asignación
        assignment = TeacherAssignment(
            teacher_id=teacher_id,
            subject_id=subject_id,
            section_id=section_id,
            academic_year_id=academic_year_id
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        flash('Asignación creada correctamente', 'success')
        return redirect(url_for('admin.assignments'))
    
    return redirect(url_for('admin.assignments'))

@admin.route('/assignments/<int:id>/edit', methods=['POST'])
@login_required
def edit_assignment(id):
    assignment = TeacherAssignment.query.get_or_404(id)
    
    if request.method == 'POST':
        teacher_id = request.form.get('teacher_id', type=int)
        subject_id = request.form.get('subject_id', type=int)
        section_id = request.form.get('section_id', type=int)
        
        # Validar que todos los campos estén presentes
        if not all([teacher_id, subject_id, section_id]):
            flash('Todos los campos son requeridos', 'danger')
            return redirect(url_for('admin.assignments'))
        
        # Verificar si ya existe una asignación igual (excepto esta misma)
        existing = TeacherAssignment.query.filter(
            TeacherAssignment.id != id,
            TeacherAssignment.teacher_id == teacher_id,
            TeacherAssignment.subject_id == subject_id,
            TeacherAssignment.section_id == section_id,
            TeacherAssignment.academic_year_id == assignment.academic_year_id
        ).first()
        
        if existing:
            flash('Ya existe una asignación con estos datos', 'danger')
            return redirect(url_for('admin.assignments'))
        
        # Actualizar asignación
        assignment.teacher_id = teacher_id
        assignment.subject_id = subject_id
        assignment.section_id = section_id
        
        db.session.commit()
        
        flash('Asignación actualizada correctamente', 'success')
        return redirect(url_for('admin.assignments'))
    
    return redirect(url_for('admin.assignments'))

@admin.route('/assignments/<int:id>/delete', methods=['POST'])
@login_required
def delete_assignment(id):
    assignment = TeacherAssignment.query.get_or_404(id)
    
    # Verificar si hay calificaciones asociadas a esta asignación
    # Esta verificación dependerá de cómo estén relacionadas las calificaciones con las asignaciones
    # Por ejemplo:
    has_grades = False
    # has_grades = StudentGrade.query.filter_by(
    #     teacher_id=assignment.teacher_id,
    #     subject_id=assignment.subject_id,
    #     # Otras condiciones según tu modelo de datos
    # ).first() is not None
    
    if has_grades:
        flash('No se puede eliminar la asignación porque tiene calificaciones asociadas', 'danger')
        return redirect(url_for('admin.assignments'))
    
    db.session.delete(assignment)
    db.session.commit()
    
    flash('Asignación eliminada correctamente', 'success')
    return redirect(url_for('admin.assignments'))

# Rutas para gestión de tipos de calificación y calificaciones de estudiantes
@admin.route('/grade-types')
@login_required
def grade_types():
    # Filtros
    subject_id = request.args.get('subject_id', type=int)
    period_id = request.args.get('period_id', type=int)
    
    # Consulta base
    query = GradeType.query
    
    # Aplicar filtros
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    if period_id:
        query = query.filter_by(period_id=period_id)
    
    # Obtener resultados
    grade_types = query.order_by(GradeType.subject_id, GradeType.period_id).all()
    
    # Preparar datos de estudiantes para cada tipo de evaluación
    grade_types_with_students = []
    for grade_type in grade_types:
        # Obtener estudiantes de la sección si existe
        students = []
        if hasattr(grade_type, 'section') and grade_type.section:
            students = Student.query.filter_by(
                section_id=grade_type.section.id, 
                is_active=True
            ).order_by(Student.last_name, Student.first_name).all()
        
        # Obtener calificaciones existentes para estos estudiantes
        existing_grades = {}
        for student in students:
            grade = StudentGrade.query.filter_by(
                student_id=student.id,
                grade_type_id=grade_type.id
            ).first()
            if grade:
                existing_grades[student.id] = grade
        
        grade_types_with_students.append({
            'grade_type': grade_type,
            'students': students,
            'existing_grades': existing_grades
        })
    
    # Obtener datos para los filtros y formularios
    subjects = Subject.query.order_by(Subject.name).all()
    academic_years = AcademicYear.query.order_by(AcademicYear.start_date.desc()).all()
    grades = Grade.query.order_by(Grade.level, Grade.name).all()
    teachers = Teacher.query.join(User).order_by(User.last_name, User.first_name).all()
    
    return render_template(
        'admin/grade_types.html', 
        title='Gestión de Evaluaciones',
        grade_types_with_students=grade_types_with_students,
        subjects=subjects,
        academic_years=academic_years,
        grades=grades,
        teachers=teachers
    )


@admin.route('/grade-types/new', methods=['POST'])
@login_required
def new_grade_type():
    if request.method == 'POST':
        name = request.form.get('name')
        weight = float(request.form.get('weight', 0)) / 100  # Convertir de porcentaje a decimal
        subject_id = request.form.get('subject_id', type=int)
        period_id = request.form.get('period_id', type=int)
        
        # Validar que todos los campos estén presentes
        if not all([name, weight, subject_id, period_id]):
            flash('Todos los campos son requeridos', 'danger')
            return redirect(url_for('admin.grade_types'))
        
        # Validar que el peso esté entre 0 y 1
        if weight <= 0 or weight > 1:
            flash('La ponderación debe estar entre 0.1% y 100%', 'danger')
            return redirect(url_for('admin.grade_types'))
        
        # Verificar que la suma de ponderaciones no exceda el 100%
        existing_types = GradeType.query.filter_by(
            subject_id=subject_id,
            period_id=period_id
        ).all()
        
        total_weight = sum(gt.weight for gt in existing_types)
        if total_weight + weight > 1:
            flash(f'La suma de ponderaciones excede el 100%. Actualmente hay un {total_weight*100:.1f}% asignado.', 'danger')
            return redirect(url_for('admin.grade_types'))
        
        # Crear nuevo tipo de calificación
        grade_type = GradeType(
            name=name,
            weight=weight,
            subject_id=subject_id,
            period_id=period_id
        )
        
        db.session.add(grade_type)
        db.session.commit()
        
        flash('Tipo de calificación creado correctamente', 'success')
        return redirect(url_for('admin.grade_types'))
    
    return redirect(url_for('admin.grade_types'))

@admin.route('/grade-types/<int:id>/edit', methods=['POST'])
@login_required
def edit_grade_type(id):
    grade_type = GradeType.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        weight = float(request.form.get('weight', 0)) / 100  # Convertir de porcentaje a decimal
        subject_id = request.form.get('subject_id', type=int)
        period_id = request.form.get('period_id', type=int)
        
        # Validar que todos los campos estén presentes
        if not all([name, weight, subject_id, period_id]):
            flash('Todos los campos son requeridos', 'danger')
            return redirect(url_for('admin.grade_types'))
        
        # Validar que el peso esté entre 0 y 1
        if weight <= 0 or weight > 1:
            flash('La ponderación debe estar entre 0.1% y 100%', 'danger')
            return redirect(url_for('admin.grade_types'))
        
        # Verificar que la suma de ponderaciones no exceda el 100%
        existing_types = GradeType.query.filter_by(
            subject_id=subject_id,
            period_id=period_id
        ).filter(GradeType.id != id).all()
        
        total_weight = sum(gt.weight for gt in existing_types)
        if total_weight + weight > 1:
            flash(f'La suma de ponderaciones excede el 100%. Actualmente hay un {total_weight*100:.1f}% asignado.', 'danger')
            return redirect(url_for('admin.grade_types'))
        
        # Actualizar tipo de calificación
        grade_type.name = name
        grade_type.weight = weight
        grade_type.subject_id = subject_id
        grade_type.period_id = period_id
        
        db.session.commit()
        
        flash('Tipo de calificación actualizado correctamente', 'success')
        return redirect(url_for('admin.grade_types'))
    
    return redirect(url_for('admin.grade_types'))

@admin.route('/grade-types/<int:id>/delete', methods=['POST'])
@login_required
def delete_grade_type(id):
    grade_type = GradeType.query.get_or_404(id)
    
    # Verificar si hay calificaciones asociadas a este tipo
    has_grades = StudentGrade.query.filter_by(grade_type_id=id).first() is not None
    
    if has_grades:
        flash('No se puede eliminar el tipo de calificación porque tiene calificaciones asociadas', 'danger')
        return redirect(url_for('admin.grade_types'))
    
    db.session.delete(grade_type)
    db.session.commit()
    
    flash('Tipo de calificación eliminado correctamente', 'success')
    return redirect(url_for('admin.grade_types'))

@admin.route('/save-student-grades', methods=['POST'])
@login_required
def save_student_grades():
    if request.method == 'POST':
        section_id = request.form.get('section_id', type=int)
        subject_id = request.form.get('subject_id', type=int)
        period_id = request.form.get('period_id', type=int)
        
        if not all([section_id, subject_id, period_id]):
            flash('Datos incompletos', 'danger')
            return redirect(url_for('admin.grade_types'))
        
        # Obtener estudiantes de la sección
        students = Student.query.filter_by(section_id=section_id, is_active=True).all()
        
        # Obtener tipos de calificación para la asignatura y período
        grade_types = GradeType.query.filter_by(subject_id=subject_id, period_id=period_id).all()
        
        # Obtener el ID del profesor (en este caso, usamos el primer profesor asignado a esta materia y sección)
        teacher_assignment = TeacherAssignment.query.filter_by(
            subject_id=subject_id,
            section_id=section_id
        ).first()
        
        if not teacher_assignment:
            flash('No hay profesor asignado a esta materia y sección', 'danger')
            return redirect(url_for('admin.grade_types', tab='student-grades', section=section_id, subject_grade=subject_id, period_grade=period_id))
        
        teacher_id = teacher_assignment.teacher_id
        
        # Procesar cada calificación
        for student in students:
            for grade_type in grade_types:
                field_name = f'grade_{student.id}_{grade_type.id}'
                grade_value = request.form.get(field_name, '')
                
                if grade_value.strip():  # Si hay un valor
                    try:
                        grade_value = float(grade_value)
                        
                        # Validar que la calificación esté en el rango correcto
                        if grade_value < 0 or grade_value > 100:
                            flash(f'La calificación para {student.get_full_name()} debe estar entre 0 y 100', 'danger')
                            continue
                        
                        # Buscar si ya existe una calificación para este estudiante, tipo y período
                        existing_grade = StudentGrade.query.filter_by(
                            student_id=student.id,
                            subject_id=subject_id,
                            grade_type_id=grade_type.id,
                            period_id=period_id
                        ).first()
                        
                        if existing_grade:
                            # Actualizar calificación existente
                            existing_grade.value = grade_value
                            existing_grade.teacher_id = teacher_id
                        else:
                            # Crear nueva calificación
                            new_grade = StudentGrade(
                                student_id=student.id,
                                subject_id=subject_id,
                                grade_type_id=grade_type.id,
                                period_id=period_id,
                                teacher_id=teacher_id,
                                value=grade_value
                            )
                            db.session.add(new_grade)
                    
                    except ValueError:
                        flash(f'Valor inválido para {student.get_full_name()}', 'danger')
        
        # Calcular y actualizar calificaciones finales
        for student in students:
            # Obtener todas las calificaciones del estudiante para esta asignatura y período
            student_grades = StudentGrade.query.filter_by(
                student_id=student.id,
                subject_id=subject_id,
                period_id=period_id
            ).all()
            
            # Calcular promedio ponderado
            total_weighted_grade = 0
            total_weight = 0
            
            for grade in student_grades:
                total_weighted_grade += grade.value * grade.grade_type.weight
                total_weight += grade.grade_type.weight
            
            # Solo actualizar si hay calificaciones
            if total_weight > 0:
                final_grade_value = total_weighted_grade / total_weight
                
                # Buscar si ya existe una calificación final
                existing_final = FinalGrade.query.filter_by(
                    student_id=student.id,
                    subject_id=subject_id,
                    period_id=period_id
                ).first()
                
                if existing_final:
                    # Actualizar calificación final existente
                    existing_final.value = final_grade_value
                else:
                    # Crear nueva calificación final
                    new_final = FinalGrade(
                        student_id=student.id,
                        subject_id=subject_id,
                        period_id=period_id,
                        value=final_grade_value
                    )
                    db.session.add(new_final)
        
        db.session.commit()
        flash('Calificaciones guardadas correctamente', 'success')
        
        # Redirigir a la misma página con los mismos filtros
        return redirect(url_for('admin.grade_types', 
                               tab='student-grades', 
                               section=section_id, 
                               subject_grade=subject_id, 
                               period_grade=period_id))
    
    return redirect(url_for('admin.grade_types'))

@admin.route('/add-grade-type-field', methods=['POST'])
@login_required
def add_grade_type_field():
    """Ruta AJAX para añadir un nuevo campo de tipo de calificación dinámicamente"""
    if request.method == 'POST':
        subject_id = request.form.get('subject_id', type=int)
        period_id = request.form.get('period_id', type=int)
        
        if not all([subject_id, period_id]):
            return jsonify({'success': False, 'message': 'Datos incompletos'})
        
        # Obtener la suma actual de ponderaciones
        existing_types = GradeType.query.filter_by(
            subject_id=subject_id,
            period_id=period_id
        ).all()
        
        total_weight = sum(gt.weight for gt in existing_types)
        remaining_weight = 1 - total_weight
        
        # Verificar si aún hay espacio para más tipos de calificación
        if remaining_weight <= 0:
            return jsonify({
                'success': False, 
                'message': 'No se pueden añadir más tipos de calificación. La suma de ponderaciones ya es 100%.'
            })
        
        # Obtener el siguiente número para el nombre por defecto
        next_number = len(existing_types) + 1
        
        # Sugerir una ponderación por defecto (el restante o 20%, lo que sea menor)
        suggested_weight = min(remaining_weight, 0.2)
        
        return jsonify({
            'success': True,
            'remaining_weight': remaining_weight * 100,  # Convertir a porcentaje
            'suggested_name': f'Evaluación {next_number}',
            'suggested_weight': suggested_weight * 100,  # Convertir a porcentaje
            'html': render_template(
                'admin/partials/grade_type_field.html',
                field_id=f'new_field_{next_number}',
                suggested_name=f'Evaluación {next_number}',
                suggested_weight=suggested_weight * 100
            )
        })
    
    return jsonify({'success': False, 'message': 'Método no permitido'})

@admin.route('/check-grade-types-weight', methods=['POST'])
@login_required
def check_grade_types_weight():
    """Ruta AJAX para verificar si la suma de ponderaciones excede el 100%"""
    if request.method == 'POST':
        subject_id = request.form.get('subject_id', type=int)
        period_id = request.form.get('period_id', type=int)
        current_id = request.form.get('current_id', type=int)
        new_weight = float(request.form.get('weight', 0)) / 100  # Convertir de porcentaje a decimal
        
        if not all([subject_id, period_id, new_weight]):
            return jsonify({'valid': False, 'message': 'Datos incompletos'})
        
        # Obtener tipos de calificación existentes, excluyendo el actual si se está editando
        query = GradeType.query.filter_by(subject_id=subject_id, period_id=period_id)
        if current_id:
            query = query.filter(GradeType.id != current_id)
        
        existing_types = query.all()
        total_weight = sum(gt.weight for gt in existing_types)
        
        # Verificar si la suma excede 1 (100%)
        if total_weight + new_weight > 1:
            return jsonify({
                'valid': False,
                'message': f'La suma de ponderaciones excede el 100%. Actualmente hay un {total_weight*100:.1f}% asignado.',
                'remaining': (1 - total_weight) * 100
            })
        
        return jsonify({
            'valid': True,
            'message': 'Ponderación válida',
            'total': (total_weight + new_weight) * 100,
            'remaining': (1 - total_weight - new_weight) * 100
        })
    
    return jsonify({'valid': False, 'message': 'Método no permitido'})

# Ruta para generar un informe de calificaciones en Excel
@admin.route('/export-grades', methods=['POST'])
@login_required
def export_grades():
    section_id = request.form.get('section_id', type=int)
    subject_id = request.form.get('subject_id', type=int)
    period_id = request.form.get('period_id', type=int)
    
    if not all([section_id, subject_id, period_id]):
        flash('Datos incompletos para generar el informe', 'danger')
        return redirect(url_for('admin.grade_types'))
    
    # Obtener datos necesarios
    section = Section.query.get_or_404(section_id)
    subject = Subject.query.get_or_404(subject_id)
    period = Period.query.get_or_404(period_id)
    
    # Obtener estudiantes de la sección
    students = Student.query.filter_by(section_id=section_id, is_active=True).order_by(Student.last_name, Student.first_name).all()
    
    # Obtener tipos de calificación para la asignatura y período
    grade_types = GradeType.query.filter_by(subject_id=subject_id, period_id=period_id).order_by(GradeType.name).all()
    
    # Obtener todas las calificaciones
    student_grades = {}
    student_averages = {}
    
    for student in students:
        grades = StudentGrade.query.filter_by(
            student_id=student.id,
            subject_id=subject_id,
            period_id=period_id
        ).all()
        
        # Organizar calificaciones por tipo
        student_grades[student.id] = {grade.grade_type_id: grade.value for grade in grades}
        
        # Calcular promedio
        total_weighted_grade = 0
        total_weight = 0
        
        for grade in grades:
            total_weighted_grade += grade.value * grade.grade_type.weight
            total_weight += grade.grade_type.weight
        
        if total_weight > 0:
            student_averages[student.id] = round(total_weighted_grade / total_weight, 2)
    
    # Crear DataFrame para Excel
    import pandas as pd
    from io import BytesIO
    
    # Preparar datos para el DataFrame
    data = []
    for student in students:
        row = {
            'Cédula': student.student_id,
            'Apellidos': student.last_name,
            'Nombres': student.first_name
        }
        
        # Añadir calificaciones por tipo
        for grade_type in grade_types:
            row[grade_type.name] = student_grades.get(student.id, {}).get(grade_type.id, '')
        
        # Añadir promedio
        row['Promedio'] = student_averages.get(student.id, '')
        
        data.append(row)
    
    # Crear DataFrame
    df = pd.DataFrame(data)
    
    # Crear archivo Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Calificaciones', index=False)
        
        # Dar formato al archivo Excel
        workbook = writer.book
        worksheet = writer.sheets['Calificaciones']
        
        # Formato para encabezados
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Aplicar formato a encabezados
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 15)
    
    # Preparar respuesta
    output.seek(0)
    
    # Nombre del archivo
    filename = f"Calificaciones_{section.grade.name}{section.name}_{subject.name}_{period.name}.xlsx"
    
    # Enviar archivo
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

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
def import_students_from_excel():
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

# Rutas para gestión de evaluaciones y calificaciones
@admin.route('/evaluations')
@login_required
def evaluations():
    # Filtros
    subject_id = request.args.get('subject_id', type=int)
    period_id = request.args.get('period_id', type=int)
    
    # Consulta base
    query = GradeType.query
    
    # Aplicar filtros
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    if period_id:
        query = query.filter_by(period_id=period_id)
    
    # Obtener resultados
    grade_types = query.order_by(GradeType.subject_id, GradeType.period_id).all()
    
    # Obtener datos para los filtros y formularios
    subjects = Subject.query.order_by(Subject.name).all()
    academic_years = AcademicYear.query.order_by(AcademicYear.start_date.desc()).all()
    grades = Grade.query.order_by(Grade.level, Grade.name).all()
    teachers = Teacher.query.join(User).order_by(User.last_name, User.first_name).all()
    
    return render_template(
        'admin/grade_types.html', 
        title='Gestión de Evaluaciones',
        grade_types=grade_types,
        subjects=subjects,
        academic_years=academic_years,
        grades=grades,
        teachers=teachers
    )

@admin.route('/evaluations/new', methods=['POST'])
@login_required
def new_evaluation():
    if request.method == 'POST':
        name = request.form.get('name')
        weight = request.form.get('weight')
        subject_id = request.form.get('subject_id')
        period_id = request.form.get('period_id')
        section_id = request.form.get('section_id')
        teacher_id = request.form.get('teacher_id')
        
        # Validar que todos los campos estén presentes
        if not all([name, weight, subject_id, period_id, section_id, teacher_id]):
            flash('Todos los campos son requeridos', 'danger')
            return redirect(url_for('admin.evaluations'))
        
        try:
            # Crear nueva evaluación
            grade_type = GradeType(
                name=name,
                weight=float(weight),
                subject_id=int(subject_id),
                period_id=int(period_id),
                section_id=int(section_id),
                teacher_id=int(teacher_id)
            )
            db.session.add(grade_type)
            db.session.commit()
            
            flash('Evaluación creada correctamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la evaluación: {str(e)}', 'danger')
        
        return redirect(url_for('admin.evaluations'))
    
    return redirect(url_for('admin.evaluations'))

@admin.route('/evaluations/<int:id>/edit', methods=['POST'])
@login_required
def edit_evaluation(id):
    grade_type = GradeType.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        weight = request.form.get('weight')
        
        # Validar que todos los campos estén presentes
        if not all([name, weight]):
            flash('Todos los campos son requeridos', 'danger')
            return redirect(url_for('admin.evaluations'))
        
        try:
            # Actualizar evaluación
            grade_type.name = name
            grade_type.weight = float(weight)
            db.session.commit()
            
            flash('Evaluación actualizada correctamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la evaluación: {str(e)}', 'danger')
        
        return redirect(url_for('admin.evaluations'))
    
    return redirect(url_for('admin.evaluations'))

@admin.route('/evaluations/<int:id>/delete', methods=['POST'])
@login_required
def delete_evaluation(id):
    grade_type = GradeType.query.get_or_404(id)
    
    try:
        # Eliminar todas las calificaciones asociadas a esta evaluación
        StudentGrade.query.filter_by(grade_type_id=id).delete()
        
        # Eliminar la evaluación
        db.session.delete(grade_type)
        db.session.commit()
        
        flash('Evaluación eliminada correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la evaluación: {str(e)}', 'danger')
    
    return redirect(url_for('admin.evaluations'))

@admin.route('/evaluations/<int:grade_type_id>/enter-grades', methods=['POST'])
@login_required
def enter_grades(grade_type_id):
    grade_type = GradeType.query.get_or_404(grade_type_id)
    
    if request.method == 'POST':
        try:
            # Obtener todos los estudiantes de la sección
            students = Student.query.filter_by(section_id=grade_type.section_id, is_active=True).all()
            
            for student in students:
                # Obtener el valor de la calificación del formulario
                grade_value = request.form.get(f'grade_{student.id}', '')
                comments = request.form.get(f'comment_{student.id}', '')
                
                # Convertir NP a 0 y validar el rango de calificaciones
                if grade_value.upper() == 'NP':
                    grade_value = 0
                elif grade_value.strip():
                    try:
                        grade_value = int(grade_value)
                        if grade_value < 1 or grade_value > 20:
                            raise ValueError("La calificación debe estar entre 1 y 20")
                    except ValueError:
                        flash(f'Calificación inválida para {student.get_full_name()}', 'danger')
                        continue
                else:
                    # Si no se proporcionó una calificación, continuar con el siguiente estudiante
                    continue
                
                # Buscar si ya existe una calificación para este estudiante en esta evaluación
                existing_grade = StudentGrade.query.filter_by(
                    student_id=student.id,
                    subject_id=grade_type.subject_id,
                    grade_type_id=grade_type_id,
                    period_id=grade_type.period_id
                ).first()
                
                if existing_grade:
                    # Actualizar calificación existente
                    existing_grade.value = grade_value
                    existing_grade.comments = comments
                else:
                    # Crear nueva calificación
                    new_grade = StudentGrade(
                        student_id=student.id,
                        subject_id=grade_type.subject_id,
                        grade_type_id=grade_type_id,
                        period_id=grade_type.period_id,
                        teacher_id=grade_type.teacher_id,
                        value=grade_value,
                        comments=comments
                    )
                    db.session.add(new_grade)
            
            db.session.commit()
            flash('Calificaciones guardadas correctamente', 'success')
            
            # Calcular calificaciones finales
            calculate_final_grades(grade_type.subject_id, grade_type.period_id, grade_type.section_id)
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar las calificaciones: {str(e)}', 'danger')
        
        return redirect(url_for('admin.evaluations'))
    
    return redirect(url_for('admin.evaluations'))

def calculate_final_grades(subject_id, period_id, section_id):
    """
    Calcula las calificaciones finales para una asignatura, período y sección específicos.
    """
    try:
        # Obtener todos los estudiantes de la sección
        students = Student.query.filter_by(section_id=section_id, is_active=True).all()
        
        # Obtener todos los tipos de evaluación para esta asignatura y período
        grade_types = GradeType.query.filter_by(
            subject_id=subject_id,
            period_id=period_id,
            section_id=section_id
        ).all()
        
        # Calcular la suma total de pesos
        total_weight = sum(gt.weight for gt in grade_types)
        
        if total_weight == 0:
            return
        
        for student in students:
            final_value = 0
            has_grades = False
            
            # Calcular la calificación final ponderada
            for grade_type in grade_types:
                student_grade = StudentGrade.query.filter_by(
                    student_id=student.id,
                    subject_id=subject_id,
                    grade_type_id=grade_type.id,
                    period_id=period_id
                ).first()
                
                if student_grade:
                    has_grades = True
                    # Calcular la contribución ponderada de esta evaluación
                    weighted_value = (student_grade.value * grade_type.weight) / total_weight
                    final_value += weighted_value
            
            if has_grades:
                # Redondear a 2 decimales
                final_value = round(final_value, 2)
                
                # Buscar si ya existe una calificación final
                existing_final = FinalGrade.query.filter_by(
                    student_id=student.id,
                    subject_id=subject_id,
                    period_id=period_id
                ).first()
                
                if existing_final:
                    # Actualizar calificación final existente
                    existing_final.value = final_value
                else:
                    # Crear nueva calificación final
                    new_final = FinalGrade(
                        student_id=student.id,
                        subject_id=subject_id,
                        period_id=period_id,
                        value=final_value
                    )
                    db.session.add(new_final)
            
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al calcular calificaciones finales: {str(e)}")

@admin.route('/save-grades', methods=['POST'])
@login_required
def save_grades():
    if request.method == 'POST':
        evaluation_id = request.form.get('evaluation_id', type=int)
        if not evaluation_id:
            flash('Evaluación no especificada', 'danger')
            return redirect(url_for('admin.evaluations', tab='grades'))
        
        # Obtener la evaluación
        grade_type = GradeType.query.get_or_404(evaluation_id)
        
        # Obtener el profesor actual (si es un profesor quien está asignando calificaciones)
        teacher_id = None
        if current_user.is_teacher():
            teacher_id = current_user.teacher_profile.id
        
        # Procesar cada calificación de estudiante
        for key, value in request.form.items():
            if key.startswith('grade_'):
                student_id = int(key.split('_')[1])
                grade_value = float(value) if value else None
                comment_key = f'comment_{student_id}'
                comment = request.form.get(comment_key, '')
                
                if grade_value is not None:
                    # Buscar si ya existe una calificación para este estudiante y evaluación
                    student_grade = StudentGrade.query.filter_by(
                        student_id=student_id,
                        grade_type_id=evaluation_id
                    ).first()
                    
                    if student_grade:
                        # Actualizar calificación existente
                        student_grade.value = grade_value
                        student_grade.comments = comment
                        student_grade.updated_at = datetime.utcnow()
                    else:
                        # Crear nueva calificación
                        student = Student.query.get(student_id)
                        if not student:
                            continue
                        
                        # Si no se especificó un profesor, intentar encontrar uno asignado
                        if not teacher_id:
                            assignment = TeacherAssignment.query.filter_by(
                                subject_id=grade_type.subject_id,
                                section_id=student.section_id
                            ).first()
                            
                            if assignment:
                                teacher_id = assignment.teacher_id
                            else:
                                flash(f'No se encontró un profesor asignado para el estudiante {student.get_full_name()}', 'warning')
                                continue
                        
                        # Crear nueva calificación
                        new_grade = StudentGrade(
                            student_id=student_id,
                            subject_id=grade_type.subject_id,
                            grade_type_id=evaluation_id,
                            period_id=grade_type.period_id,
                            teacher_id=teacher_id,
                            value=grade_value,
                            comments=comment
                        )
                        db.session.add(new_grade)
        
        # Guardar cambios
        db.session.commit()
        
        # Actualizar calificaciones finales
        update_final_grades(grade_type.subject_id, grade_type.period_id)
        
        flash('Calificaciones guardadas correctamente', 'success')
        return redirect(url_for('admin.evaluations', tab='grades', evaluation=evaluation_id))
    
    return redirect(url_for('admin.evaluations', tab='grades'))

def update_final_grades(subject_id, period_id):
    """Actualiza las calificaciones finales para una asignatura y período"""
    # Obtener todos los estudiantes que tienen calificaciones para esta asignatura y período
    student_ids = db.session.query(StudentGrade.student_id).filter_by(
        subject_id=subject_id,
        period_id=period_id
    ).distinct().all()
    
    student_ids = [id[0] for id in student_ids]
    
    # Para cada estudiante, calcular su calificación final
    for student_id in student_ids:
        # Obtener todas las calificaciones del estudiante para esta asignatura y período
        grades = StudentGrade.query.filter_by(
            student_id=student_id,
            subject_id=subject_id,
            period_id=period_id
        ).all()
        
        # Calcular promedio ponderado
        total_weighted_grade = 0
        total_weight = 0
        
        for grade in grades:
            grade_type = GradeType.query.get(grade.grade_type_id)
            total_weighted_grade += grade.value * grade_type.weight
            total_weight += grade_type.weight
        
        # Si hay ponderación, calcular promedio
        if total_weight > 0:
            final_value = round(total_weighted_grade / total_weight, 2)
            
            # Buscar si ya existe una calificación final
            final_grade = FinalGrade.query.filter_by(
                student_id=student_id,
                subject_id=subject_id,
                period_id=period_id
            ).first()
            
            if final_grade:
                # Actualizar calificación final existente
                final_grade.value = final_value
                final_grade.updated_at = datetime.utcnow()
            else:
                # Crear nueva calificación final
                new_final = FinalGrade(
                    student_id=student_id,
                    subject_id=subject_id,
                    period_id=period_id,
                    value=final_value
                )
                db.session.add(new_final)
    
    # Guardar cambios
    db.session.commit()

# API endpoints para el frontend
@admin.route('/api/section/<int:section_id>/teachers')
@login_required
def api_section_teachers(section_id):
    """Obtiene los profesores asignados a una sección"""
    teachers = db.session.query(Teacher).join(
        TeacherAssignment, Teacher.id == TeacherAssignment.teacher_id
    ).filter(
        TeacherAssignment.section_id == section_id
    ).distinct().all()
    
    return jsonify({
        'teachers': [
            {
                'id': teacher.id,
                'name': f"{teacher.user.first_name} {teacher.user.last_name}"
            }
            for teacher in teachers
        ]
    })

@admin.route('/api/teacher/<int:teacher_id>/section/<int:section_id>/subjects')
@login_required
def api_teacher_section_subjects(teacher_id, section_id):
    """Obtiene las asignaturas asignadas a un profesor en una sección"""
    subjects = db.session.query(Subject).join(
        TeacherAssignment, Subject.id == TeacherAssignment.subject_id
    ).filter(
        TeacherAssignment.teacher_id == teacher_id,
        TeacherAssignment.section_id == section_id
    ).all()
    
    return jsonify({
        'subjects': [
            {
                'id': subject.id,
                'name': subject.name
            }
            for subject in subjects
        ]
    })

# @admin.route('/api/academic-year/<int:year_id>/periods')
# @login_required
# def api_academic_year_periods(year_id):
#     # Obtiene los períodos de un año académico
#     periods = Period.query.filter_by(academic_year_id=year_id).order_by(Period.start_date).all()
    
#     return jsonify({
#         'periods': [
#             {
#                 'id': period.id,
#                 'name': period.name
#             }
#             for period in periods
#         ]
#     })

@admin.route('/api/section/<int:section_id>/subject/<int:subject_id>/evaluations')
@login_required
def api_section_subject_evaluations(section_id, subject_id):
    """Obtiene las evaluaciones para una sección y asignatura"""
    # Primero obtenemos los períodos activos
    active_year = AcademicYear.query.filter_by(is_active=True).first()
    if not active_year:
        return jsonify({'evaluations': []})
    
    periods = Period.query.filter_by(academic_year_id=active_year.id).all()
    period_ids = [p.id for p in periods]
    
    # Luego obtenemos las evaluaciones
    evaluations = GradeType.query.filter(
        GradeType.subject_id == subject_id,
        GradeType.period_id.in_(period_ids)
    ).all()
    
    return jsonify({
        'evaluations': [
            {
                'id': eval.id,
                'name': eval.name,
                'weight': eval.weight * 100
            }
            for eval in evaluations
        ]
    })

# Ruta para configuración de períodos académicos
@admin.route('/periods')
@login_required
def periods():
    academic_years = AcademicYear.query.order_by(AcademicYear.start_date.desc()).all()
    # Crear un formulario vacío para usar en los modales
    form = PeriodForm()
    form.academic_year_id.choices = [(y.id, y.name) for y in academic_years]
    
    return render_template('admin/periods.html', title='Períodos Académicos', academic_years=academic_years, form=form)

@admin.route('/periods/new', methods=['POST'])
@login_required
def new_period():
    form = PeriodForm()
    form.academic_year_id.choices = [(y.id, y.name) for y in AcademicYear.query.all()]
    
    if form.validate_on_submit():
        period = Period(
            name=form.name.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            academic_year_id=form.academic_year_id.data
        )
        db.session.add(period)
        db.session.commit()
        flash('Período creado correctamente', 'success')
        return redirect(url_for('admin.periods'))
    
    # Si hay errores de validación, mostrarlos
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'Error en {getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('admin.periods'))

@admin.route('/periods/<int:id>/edit', methods=['POST'])
@login_required
def edit_period(id):
    period = Period.query.get_or_404(id)
    
    # Crear el formulario y establecer las opciones para academic_year_id
    form = PeriodForm()
    form.academic_year_id.choices = [(y.id, y.name) for y in AcademicYear.query.all()]
    
    # Procesar el formulario manualmente ya que viene de un modal
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            academic_year_id = int(request.form.get('academic_year_id'))
            
            # Validaciones manuales
            if not name or not start_date or not end_date or not academic_year_id:
                flash('Todos los campos son requeridos', 'danger')
                return redirect(url_for('admin.periods'))
                
            if end_date <= start_date:
                flash('La fecha de fin debe ser posterior a la fecha de inicio', 'danger')
                return redirect(url_for('admin.periods'))
            
            # Actualizar el período
            period.name = name
            period.start_date = start_date
            period.end_date = end_date
            period.academic_year_id = academic_year_id
            
            db.session.commit()
            flash('Período actualizado correctamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el período: {str(e)}', 'danger')
        
        return redirect(url_for('admin.periods'))
    
    return redirect(url_for('admin.periods'))

@admin.route('/periods/<int:id>/delete', methods=['POST'])
@login_required
def delete_period(id):
    period = Period.query.get_or_404(id)
    
    # Verificar si hay evaluaciones o calificaciones asociadas
    if GradeType.query.filter_by(period_id=id).first() or StudentGrade.query.filter_by(period_id=id).first():
        flash('No se puede eliminar este período porque tiene evaluaciones o calificaciones asociadas', 'danger')
        return redirect(url_for('admin.periods'))
    
    db.session.delete(period)
    db.session.commit()
    flash('Período eliminado correctamente', 'success')
    return redirect(url_for('admin.periods'))

@admin.route('/api/academic-year/<int:year_id>/periods')
@login_required
def api_periods(year_id):
    try:
        # Verificar que el año académico existe
        academic_year = AcademicYear.query.get_or_404(year_id)
        
        # Obtener períodos del año académico
        periods = Period.query.filter_by(academic_year_id=year_id).order_by(Period.start_date).all()
        
        return jsonify({
            'success': True,
            'periods': [
                {
                    'id': period.id,
                    'name': period.name,
                    'start_date': period.start_date.strftime('%Y-%m-%d'),
                    'end_date': period.end_date.strftime('%Y-%m-%d')
                }
                for period in periods
            ]
        })
    except Exception as e:
        current_app.logger.error(f"Error en api_periods para año {year_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error al obtener períodos: {str(e)}'
        }), 500

@admin.route('/api/subject/<int:subject_id>/period/<int:period_id>/available-weight')
@login_required
def api_available_weight(subject_id, period_id):
    try:
        # Obtener parámetros adicionales de la consulta
        section_id = request.args.get('section_id', type=int)
        teacher_id = request.args.get('teacher_id', type=int)
        
        # Verificar que la asignatura y el período existen
        subject = Subject.query.get_or_404(subject_id)
        period = Period.query.get_or_404(period_id)
        
        # Construir el filtro base
        filter_criteria = {
            'subject_id': subject_id,
            'period_id': period_id
        }
        
        # Añadir criterios adicionales si están presentes
        if section_id:
            filter_criteria['section_id'] = section_id
            
        if teacher_id:
            filter_criteria['teacher_id'] = teacher_id
        
        # Calcular la ponderación total ya asignada
        grade_types = GradeType.query.filter_by(**filter_criteria).all()
        
        # Imprimir los valores para depuración
        weights = [gt.weight for gt in grade_types]
        current_app.logger.info(f"Valores de weight en la base de datos: {weights}")
        
        total_weight = sum(weights)
        available_weight = 100.0 - total_weight
        
        return jsonify({
            'success': True,
            'total_weight': total_weight,
            'available_weight': available_weight,
            'evaluations': [{'id': gt.id, 'name': gt.name, 'weight': gt.weight} for gt in grade_types],
            'filter_applied': {
                'subject_id': subject_id,
                'period_id': period_id,
                'section_id': section_id,
                'teacher_id': teacher_id
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error en api_available_weight: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error al calcular ponderación disponible: {str(e)}'
        }), 500

# Ruta API para obtener grados asociados a una asignatura
@admin.route('/api/subject/<int:subject_id>/grades')
@login_required
def api_subject_grades(subject_id):
    try:
        # Verificar que la asignatura existe
        subject = Subject.query.get_or_404(subject_id)
        
        # En un sistema real, aquí obtendrías los grados asociados a la asignatura
        # Por ahora, simplemente devolvemos todos los grados
        grades = Grade.query.order_by(Grade.level, Grade.name).all()
        
        return jsonify({
            'success': True,
            'grades': [
                {
                    'id': grade.id,
                    'name': grade.name,
                    'level': grade.level
                }
                for grade in grades
            ]
        })
    except Exception as e:
        current_app.logger.error(f"Error en api_subject_grades para asignatura {subject_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error al obtener grados: {str(e)}'
        }), 500

# Ruta API para obtener secciones de un grado
@admin.route('/api/grade/<int:grade_id>/sections')
@login_required
def api_grade_sections(grade_id):
    try:
        # Verificar que el grado existe
        grade = Grade.query.get_or_404(grade_id)
        
        # Obtener secciones del grado
        sections = Section.query.filter_by(grade_id=grade_id).order_by(Section.name).all()
        
        return jsonify({
            'success': True,
            'sections': [
                {
                    'id': section.id,
                    'name': section.name,
                    'grade_id': section.grade_id
                }
                for section in sections
            ]
        })
    except Exception as e:
        current_app.logger.error(f"Error en api_grade_sections para grado {grade_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error al obtener secciones: {str(e)}'
        }), 500

# Ruta API para obtener profesores asignados a una combinación de asignatura, sección y año académico
@admin.route('/api/assignments')
@login_required
def api_assignments():
    try:
        # Obtener parámetros
        subject_id = request.args.get('subject_id', type=int)
        section_id = request.args.get('section_id', type=int)
        academic_year_id = request.args.get('academic_year_id', type=int)
        
        if not subject_id or not section_id or not academic_year_id:
            return jsonify({
                'success': False,
                'message': 'Se requieren los parámetros subject_id, section_id y academic_year_id'
            }), 400
        
        # Buscar asignaciones que coincidan con los criterios
        assignments = TeacherAssignment.query.filter_by(
            subject_id=subject_id,
            section_id=section_id,
            academic_year_id=academic_year_id
        ).all()
        
        # Obtener los profesores de esas asignaciones
        teachers = []
        for assignment in assignments:
            teacher = Teacher.query.get(assignment.teacher_id)
            if teacher and teacher.user:
                teachers.append({
                    'id': teacher.id,
                    'name': f"{teacher.user.first_name} {teacher.user.last_name}",
                    'specialization': teacher.specialization
                })
        
        return jsonify({
            'success': True,
            'teachers': teachers
        })
    except Exception as e:
        current_app.logger.error(f"Error en api_assignments: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error al obtener profesores asignados: {str(e)}'
        }), 500

# Ruta API para obtener años académicos
@admin.route('/api/academic-years')
@login_required
def api_academic_years():
    try:
        academic_years = AcademicYear.query.order_by(AcademicYear.start_date.desc()).all()
        
        return jsonify({
            'success': True,
            'academic_years': [
                {
                    'id': year.id,
                    'name': year.name,
                    'start_date': year.start_date.strftime('%Y-%m-%d'),
                    'end_date': year.end_date.strftime('%Y-%m-%d'),
                    'is_active': year.is_active
                }
                for year in academic_years
            ]
        })
    except Exception as e:
        current_app.logger.error(f"Error en api_academic_years: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error al obtener años académicos: {str(e)}'
        }), 500

# Ruta API para obtener períodos de un año académico
@admin.route('/api/academic-year/<int:year_id>/periods')
@login_required
def api_academic_year_periods(year_id):
    try:
        # Verificar que el año académico existe
        year = AcademicYear.query.get_or_404(year_id)
        
        # Obtener períodos del año académico
        periods = Period.query.filter_by(academic_year_id=year_id).order_by(Period.start_date).all()
        
        return jsonify({
            'success': True,
            'periods': [
                {
                    'id': period.id,
                    'name': period.name,
                    'start_date': period.start_date.strftime('%Y-%m-%d'),
                    'end_date': period.end_date.strftime('%Y-%m-%d')
                }
                for period in periods
            ]
        })
    except Exception as e:
        current_app.logger.error(f"Error en api_academic_year_periods para año {year_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error al obtener períodos: {str(e)}'
        }), 500
