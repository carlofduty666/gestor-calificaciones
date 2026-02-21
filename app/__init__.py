from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from datetime import datetime

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor inicie sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    from app.models.users import User
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    # Registrar blueprints
    from app.routes.auth import auth as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.routes.admin import admin as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.routes.teacher import teacher as teacher_bp
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    
    from app.routes.reports import reports as reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')

    from app.routes.templates import templates as templates_bp
    app.register_blueprint(templates_bp, url_prefix='/templates')
    
    from app.routes.data_import import data_import as data_import_bp
    app.register_blueprint(data_import_bp, url_prefix='/import')
    
    # Ruta raíz que maneja DEMO_MODE
    from flask import redirect, url_for, current_app
    from flask_login import login_user, current_user, logout_user
    
    @app.route('/')
    def index():
        """
        Ruta raíz que maneja la redirección según el estado de autenticación y DEMO_MODE.
        
        EN DEMO_MODE (IMPORTANTE):
        - SIEMPRE hacer logout de cualquier sesión previa
        - Hacer login automático con el usuario demo (admin)
        - Redirigir a /admin/dashboard
        
        En modo normal:
        - Si autenticado: redirigir según rol (admin o teacher)
        - Si no autenticado: redirigir a login
        """
        # 1. En DEMO_MODE, SIEMPRE asegurar que es el usuario demo
        if current_app.config.get('DEMO_MODE'):
            # Primero, hacer logout de cualquier sesión previa
            logout_user()
            
            # Luego, hacer login con el usuario demo
            try:
                demo_user = User.query.filter_by(email='demo@example.com').first()
                if demo_user and demo_user.role == 'admin':
                    login_user(demo_user, remember=True)
                    return redirect(url_for('admin.dashboard'))
            except Exception as e:
                current_app.logger.error(f"Error en login automático DEMO: {str(e)}")
        
        # 2. Si está autenticado (en modo normal), redirigir al dashboard correspondiente
        if current_user.is_authenticated:
            if current_user.is_admin():
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('teacher.dashboard'))
        
        # 3. Si no está autenticado, redirigir a login
        return redirect(url_for('auth.login'))
    
    # Crear directorios necesarios
    import os
    upload_dirs = [
        'uploads',
        'uploads/imports',
        'uploads/exports'
    ]
    
    for directory in upload_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    return app
