from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Curso, Estudiante, Calificacion
from app import db

profesor = Blueprint('profesor', __name__)

@profesor.route('/dashboard')
@login_required
def dashboard():
    if current_user.tipo != 'profesor':
        flash('Acceso no autorizado')
        return redirect(url_for('auth.login'))
    
    cursos = Curso.query.filter_by(profesor_id=current_user.id).all()
    return render_template('profesor/dashboard.html', cursos=cursos)

@profesor.route('/curso/<int:curso_id>')
@login_required
def ver_curso(curso_id):
    if current_user.tipo != 'profesor':
        flash('Acceso no autorizado')
        return redirect(url_for('auth.login'))
    
    curso = Curso.query.get_or_404(curso_id)
    if curso.profesor_id != current_user.id:
        flash('No tienes permiso para ver este curso')
        return redirect(url_for('profesor.dashboard'))
    
    estudiantes = Estudiante.query.join(Calificacion).filter(Calificacion.curso_id == curso_id).all()
    return render_template('profesor/curso.html', curso=curso, estudiantes=estudiantes)

@profesor.route('/calificacion/nueva', methods=['GET', 'POST'])
@login_required
def nueva_calificacion():
    if current_user.tipo != 'profesor':
        flash('Acceso no autorizado')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        estudiante_id = request.form.get('estudiante_id')
        curso_id = request.form.get('curso_id')
        valor = request.form.get('valor')
        observacion = request.form.get('observacion')
        
        curso = Curso.query.get_or_404(curso_id)
        if curso.profesor_id != current_user.id:
            flash('No tienes permiso para calificar en este curso')
            return redirect(url_for('profesor.dashboard'))
        
        calificacion = Calificacion(
            valor=float(valor),
            observacion=observacion,
            estudiante_id=estudiante_id,
            curso_id=curso_id
        )
        
        db.session.add(calificacion)
        db.session.commit()
        
        flash('Calificación registrada correctamente')
        return redirect(url_for('profesor.ver_curso', curso_id=curso_id))
    
    cursos = Curso.query.filter_by(profesor_id=current_user.id).all()
    estudiantes = Estudiante.query.all()
    
    return render_template('profesor/nueva_calificacion.html', cursos=cursos, estudiantes=estudiantes)
