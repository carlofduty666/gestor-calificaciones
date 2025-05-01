import mysql.connector
from mysql.connector import Error
from app.config import Config
from app import create_app, db
import os

def create_database():
    # Crea la base de datos
    try:
        # Extraer configuración
        config = Config()
        db_user = config.DB_USER
        db_password = config.DB_PASSWORD
        db_host = config.DB_HOST
        db_name = config.DB_NAME

        # Conectar a la base de datos con MySQL
        connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password
        )

        if connection.is_connected():
            cursor = connection.cursor() # un cursor es un objeto que permite interactuar con la base de datos.

            # Verificar si la base de datos existe
            cursor.execute(f"SHOW DATABASES LIKE '{db_name}'") 
            result = cursor.fetchone() # fetchone() es un método que devuelve el primer registro de una consulta.

            if not result:
                cursor.execute(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"Base de datos '{db_name}' creada exitosamente")
            else:
                print(f"La base de datos '{db_name}' ya existe")
                
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return False

    if __name__ == '__main__':
        if create_database():
            # Inicializar la aplicación Flask
            app = create_app()

        # Crear directorio de migraciones si no existe
        if not os.path.exists('migrations'):
            os.system('flask db init')
        
        # Generar migración y actualizar la base de datos
        os.system('flask db migrate -m "Migración inicial"')
        os.system('flask db upgrade')
        
        print("Base de datos inicializada correctamente")