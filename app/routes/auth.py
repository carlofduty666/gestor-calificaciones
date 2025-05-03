from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.users import User
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
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Usuario o contraseña incorrectos', 'danger')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        
        # Reemplazar la lógica que usa url_parse
        # if not next_page or url_parse(next_page).netloc != '':
        
        # Por esta lógica más simple:
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
