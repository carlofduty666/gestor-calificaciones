from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from app.config import Config

db = SQLAlchemy() # Crea una instancia de SQLAlchemy
migrate = Migrate() # Crea una instancia de Migrate
login_manager = LoginManager() # Crea una instancia de LoginManager
login_manager.login_view = 'auth.logih' # Establece la vista de inicio de sesión

def create_app(config_class=Config): # Crea una aplicación Flask
    app = Flask(__name__)
    app.config.from_object(config_class) # Carga la configuración de la aplicación

    db.init_app(app) # Inicializa la base de datos
    migrate.init_app(app, db) # Inicializa la migración
    login_manager.init_app(app) # Inicializa el login manager

    # el blueprint es un conjunto de rutas y vistas que se pueden agrupar y reutilizar en una aplicación Flask.
    from app.routes.auth import auth as auth_blueprint # Importa el blueprint de autenticación
    from app.routes.profesor import profesor as profesor_blueprint # Importa el blueprint de profesor
    from app.routes.admin import admin as admin_blueprint # Importa el blueprint de administrador
    

    app.register_blueprint(auth_blueprint) # Registra el blueprint de autenticación
    app.register_blueprint(profesor_blueprint, url_prefix='/profesor')  # Registra el blueprint de profesor
    app.register_blueprint(admin_blueprint, url_prefix='/admin') # Registra el blueprint de administrador
    
    return app