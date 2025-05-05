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
    
    return app
