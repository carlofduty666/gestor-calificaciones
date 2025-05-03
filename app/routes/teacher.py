from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.users import User
from app.models.academic import AcademicYear, Period, Grade, Section, Subject, Student, Teacher, TeacherAssignment
from app.models.grades import GradeType, StudentGrade, FinalGrade
from app.forms.teacher_forms import GradeForm, FinalGradeForm
from app import db

teacher = Blueprint('teacher', __name__)

@teacher.before_request
def check_teacher():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    if not current_user.is_teacher() and not current_user.is_admin():
        flash('Acceso no autorizado. Se requiere ser profesor.', 'danger')
        return redirect(url_for('auth.login'))

@teacher.route('/dashboard')
@login_required
def dashboard():
    # Obtener perfil de profesor
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    
    if not teacher:
        flash('No se encontró un perfil de profesor para este usuario', 'warning')
        return redirect(url_for('auth.logout'))
    
    # Año académico activo
    active_year = AcademicYear.query.filter_by(is_active=True).first()
    
    if not active_year:
        flash('No hay un año académico activo configurado', 'warning')
        return render_template('teacher/dashboard.html', title='Panel de Profesor', assignments=[])
    
    # Obtener asignaciones del profesor en el año activo
    assignments = TeacherAssignment.query.filter_by(
        teacher_id=teacher.id,
        academic_year_id=active_year.id
    ).all()
    
    return render_template('teacher/dashboard.html', title='Panel de Profesor', 
                          assignments=assignments, active_year=active_year)

@teacher.route('/assignments/<int:assignment_id>/students')
@login_required
def assignment_students(assignment_id):
    assignment = TeacherAssignment.query.get_or_404(assignment_id)
    
    # Verificar que la asignación pertenece al profesor actual
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if assignment.teacher_id != teacher.id and not current_user.is_admin():
        flash('No tienes permiso para ver esta asignación', 'danger')
        return redirect(url_for('teacher.dashboard'))
    
    # Obtener estudiantes de la sección
    students = Student.query.filter_by(
        section_id=assignment.section_id,
        is_active=True
    ).order_by(Student.last_name).all()
    
    # Obtener períodos del año académico
    periods = Period.query.filter_by(
        academic_year_id=assignment.academic_year_id
    ).order_by(Period.start_date).all()
    
    return render_template('teacher/assignment_students.html', 
                          title=f'Estudiantes - {assignment.subject.name} - {assignment.section.grade.name}{assignment.section.name}',
                          assignment=assignment,
                          students=students,
                          periods=periods)

@teacher.route('/assignments/<int:assignment_id>/grades/<int:period_id>')
@login_required
def view_grades(assignment_id, period_id):
    assignment = TeacherAssignment.query.get_or_404(assignment_id)
    period = Period.query.get_or_404(period_id)
    
    # Verificar que la asignación pertenece al profesor actual
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if assignment.teacher_id != teacher.id and not current_user.is_admin():
        flash('No tienes permiso para ver esta asignación', 'danger')
        return redirect(url_for('teacher.dashboard'))
    
    # Obtener estudiantes de la sección
    students = Student.query.filter_by(
        section_id=assignment.section_id,
        is_active=True
    ).order_by(Student.last_name).all()
    
    # Obtener tipos de calificación para esta asignatura y período
    grade_types = GradeType.query.filter_by(
        subject_id=assignment.subject_id,
        period_id=period_id
    ).order_by(GradeType.name).all()
    
    # Obtener calificaciones existentes
    grades = {}
    for student in students:
        grades[student.id] = {}
        for grade_type in grade_types:
            grade = StudentGrade.query.filter_by(
                student_id=student.id,
                subject_id=assignment.subject_id,
                grade_type_id=grade_type.id,
                period_id=period_id,
                teacher_id=teacher.id
            ).first()
            
            if grade:
                grades[student.id][grade_type.id] = grade.value
    
    # Obtener calificaciones finales
    final_grades = {}
    for student in students:
        final_grade = FinalGrade.query.filter_by(
            student_id=student.id,
            subject_id=assignment.subject_id,
            period_id=period_id
        ).first()
        
        if final_grade:
            final_grades[student.id] = final_grade.value
    
    return render_template('teacher/view_grades.html',
                          title=f'Calificaciones - {assignment.subject.name} - {period.name}',
                          assignment=assignment,
                          period=period,
                          students=students,
                          grade_types=grade_types,
                          grades=grades,
                          final_grades=final_grades)

@teacher.route('/assignments/<int:assignment_id>/student/<int:student_id>/period/<int:period_id>/grade', methods=['GET', 'POST'])
@login_required
def enter_grade(assignment_id, student_id, period_id):
    assignment = TeacherAssignment.query.get_or_404(assignment_id)
    student = Student.query.get_or_404(student_id)
    period = Period.query.get_or_404(period_id)
    
    # Verificar que la asignación pertenece al profesor actual
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if assignment.teacher_id != teacher.id and not current_user.is_admin():
        flash('No tienes permiso para esta acción', 'danger')
        return redirect(url_for('teacher.dashboard'))
    
    # Obtener tipos de calificación para esta asignatura y período
    grade_types = GradeType.query.filter_by(
        subject_id=assignment.subject_id,
        period_id=period_id
    ).order_by(GradeType.name).all()
    
    form = GradeForm()
    
    # Crear campos dinámicos para cada tipo de calificación
    for grade_type in grade_types:
        field_name = f'grade_{grade_type.id}'
        setattr(GradeForm, field_name, FloatField(
            grade_type.name,
            validators=[Optional(), NumberRange(min=0, max=100)]
        ))
        form = GradeForm()
    
    if form.validate_on_submit():
        for grade_type in grade_types:
            field_name = f'grade_{grade_type.id}'
            value = getattr(form, field_name).data
            
            if value is not None:
                # Buscar si ya existe una calificación
                grade = StudentGrade.query.filter_by(
                    student_id=student.id,
                    subject_id=assignment.subject_id,
                    grade_type_id=grade_type.id,
                    period_id=period_id,
                    teacher_id=teacher.id
                ).first()
                
                if grade:
                    grade.value = value
                    grade.comments = form.comments.data
                else:
                    grade = StudentGrade(
                        student_id=student.id,
                        subject_id=assignment.subject_id,
                        grade_type_id=grade_type.id,
                        period_id=period_id,
                        teacher_id=teacher.id,
                        value=value,
                        comments=form.comments.data
                    )
                    db.session.add(grade)
        
        db.session.commit()
        flash('Calificaciones guardadas correctamente', 'success')
        return redirect(url_for('teacher.view_grades', assignment_id=assignment_id, period_id=period_id))
    
    # Cargar valores existentes
    for grade_type in grade_types:
        field_name = f'grade_{grade_type.id}'
        grade = StudentGrade.query.filter_by(
            student_id=student.id,
            subject_id=assignment.subject_id,
            grade_type_id=grade_type.id,
            period_id=period_id,
            teacher_id=teacher.id
        ).first()
        
        if grade and hasattr(form, field_name):
            getattr(form, field_name).data = grade.value
            form.comments.data = grade.comments
    
    return render_template('teacher/enter_grade.html',
                          title=f'Calificaciones - {student.first_name} {student.last_name}',
                          form=form,
                          assignment=assignment,
                          student=student,
                          period=period,
                          grade_types=grade_types)

@teacher.route('/assignments/<int:assignment_id>/period/<int:period_id>/final-grades', methods=['GET', 'POST'])
@login_required
def enter_final_grades(assignment_id, period_id):
    assignment = TeacherAssignment.query.get_or_404(assignment_id)
    period = Period.query.get_or_404(period_id)
    
    # Verificar que la asignación pertenece al profesor actual
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if assignment.teacher_id != teacher.id and not current_user.is_admin():
        flash('No tienes permiso para esta acción', 'danger')
        return redirect(url_for('teacher.dashboard'))
    
    # Obtener estudiantes de la sección
    students = Student.query.filter_by(
        section_id=assignment.section_id,
        is_active=True
    ).order_by(Student.last_name).all()
    
    # Obtener tipos de calificación para esta asignatura y período
    grade_types = GradeType.query.filter_by(
        subject_id=assignment.subject_id,
        period_id=period_id
    ).all()
    
    if request.method == 'POST':
        for student in students:
            final_value = request.form.get(f'final_{student.id}')
            comments = request.form.get(f'comments_{student.id}')
            
            if final_value:
                # Buscar si ya existe una calificación final
                final_grade = FinalGrade.query.filter_by(
                    student_id=student.id,
                    subject_id=assignment.subject_id,
                    period_id=period_id
                ).first()
                
                if final_grade:
                    final_grade.value = float(final_value)
                    final_grade.comments = comments
                else:
                    final_grade = FinalGrade(
                        student_id=student.id,
                        subject_id=assignment.subject_id,
                        period_id=period_id,
                        value=float(final_value),
                        comments=comments
                    )
                    db.session.add(final_grade)
        
        db.session.commit()
        flash('Calificaciones finales guardadas correctamente', 'success')
        return redirect(url_for('teacher.view_grades', assignment_id=assignment_id, period_id=period_id))
    
    # Calcular calificaciones finales propuestas
    proposed_finals = {}
    existing_finals = {}
    
    for student in students:
        # Obtener calificaciones existentes
        student_grades = {}
        for grade_type in grade_types:
            grade = StudentGrade.query.filter_by(
                student_id=student.id,
                subject_id=assignment.subject_id,
                grade_type_id=grade_type.id,
                period_id=period_id
            ).first()
            
            if grade:
                student_grades[grade_type.id] = {
                    'value': grade.value,
                    'weight': grade_type.weight
                }
        
        # Calcular promedio ponderado
        if student_grades:
            total_value = 0
            total_weight = 0
            
            for grade_data in student_grades.values():
                total_value += grade_data['value'] * grade_data['weight']
                total_weight += grade_data['weight']
            
            if total_weight > 0:
                proposed_finals[student.id] = round(total_value / total_weight, 2)
        
        # Obtener calificación final existente
        final_grade = FinalGrade.query.filter_by(
            student_id=student.id,
            subject_id=assignment.subject_id,
            period_id=period_id
        ).first()
        
        if final_grade:
            existing_finals[student.id] = {
                'value': final_grade.value,
                'comments': final_grade.comments
            }
    
    return render_template('teacher/enter_final_grades.html',
                          title=f'Calificaciones Finales - {assignment.subject.name} - {period.name}',
                          assignment=assignment,
                          period=period,
                          students=students,
                          proposed_finals=proposed_finals,
                          existing_finals=existing_finals)
