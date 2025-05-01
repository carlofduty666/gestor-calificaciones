from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import Usuario
from app import db
from werkzeug.urls import url_parse

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.tipo == 'profesor':
            return redirect(url_for('profesor.dashboard'))
        else:
            return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = Usuario.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Usuario o contraseña incorrectos')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            if user.tipo == 'profesor':
                next_page = url_for('profesor.dashboard')
            else:
                next_page = url_for('admin.dashboard')
        
        return redirect(next_page)
    
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
