from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.users import User
from app.models.academic import Admin
from app.forms.auth_forms import LoginForm, RegistrationForm
from app import db

# Eliminar completamente esta línea:
# from werkzeug.urls import url_parse

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('teacher.dashboard'))
            
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(identification_number=form.identification_number.data).first()
        if user is None or not user.check_password(form.password.data) or not user.is_registered:
            flash('Cédula o contraseña incorrectos', 'danger')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or '//' in next_page:
            if user.is_admin():
                next_page = url_for('admin.dashboard')
            else:
                next_page = url_for('teacher.dashboard')
        return redirect(next_page)
        
    return render_template('auth/login.html', title='Iniciar Sesión', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('teacher.dashboard'))
            
    form = RegistrationForm()
    if form.validate_on_submit():
        # Buscar si existe un pre-registro con esta cédula
        user = User.query.filter_by(
            identification_number=form.identification_number.data,
            is_registered=False
        ).first()
        
        if user:
            # Actualizar el usuario pre-registrado
            user.email = form.email.data
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.set_password(form.password.data)
            user.is_registered = True
            
            db.session.commit()
            flash('¡Registro completado con éxito! Ahora puede iniciar sesión', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('No se encontró un pre-registro con esta cédula o ya está registrado', 'danger')
            
    return render_template('auth/register.html', title='Completar Registro', form=form)

@auth.route('/setup-admin', methods=['GET', 'POST'])
def setup_admin():
    # Verificar si ya existe un administrador
    if User.query.filter_by(role='admin').first():
        flash('Ya existe un administrador en el sistema', 'warning')
        return redirect(url_for('auth.login'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        # Crear usuario administrador
        admin = User(
            identification_number=form.identification_number.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role='admin',
            is_registered=True
        )
        admin.set_password(form.password.data)
        db.session.add(admin)
        
        # Crear perfil de administrador
        admin_profile = Admin(user=admin, department='Administración')
        db.session.add(admin_profile)
        
        db.session.commit()
        flash('Administrador creado correctamente. Ahora puede iniciar sesión', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/setup_admin.html', title='Configurar Administrador', form=form)