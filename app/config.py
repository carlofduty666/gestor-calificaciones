import os # Importa el módulo os, el cual es un módulo estándar de Python que proporciona una forma de interactuar con el sistema operativo.

class Config:
    # Configuración de la aplicación
    # environ es un diccionario que contiene las variables de entorno del sistema operativo.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'root'
    DB_USER = os.envirob.get('DB_USER') or 'root'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or ''
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_NAME = os.environ.get('DB_NAME') or 'gestor_calificaciones'

    # Establece la URI de la base de datos
    SQLALCHEMY_DATABASE_URI = f'mysql://root:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
     # Desactiva el seguimiento de modificaciones de SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False