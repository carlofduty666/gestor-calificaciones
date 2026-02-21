# Guía Completa: Migrar a Supabase

## Fase 1: Preparación en Supabase

### Paso 1.1: Crear cuenta en Supabase
1. Ve a https://supabase.com
2. Haz clic en **"Sign Up"**
3. Usa tu email o GitHub
4. Verifica tu email

### Paso 1.2: Crear un nuevo proyecto
1. En el dashboard, haz clic en **"New Project"**
2. Configura:
   - **Name:** `gestor-calificaciones` (o tu preferencia)
   - **Database Password:** Genera una contraseña fuerte (cópiala, la necesitarás)
   - **Region:** Elige la región más cercana a ti (ej: `us-east-1`)
   - **Pricing Plan:** `Free` (tiene límites pero es suficiente para demo)
3. Haz clic en **"Create new project"**

⏰ **Espera 2-3 minutos** a que el proyecto se inicialice

### Paso 1.3: Obtener los datos de conexión
1. En tu proyecto, ve a **Settings → Database**
2. Busca la sección **"Connection Strings"**
3. Ver la opción **"URI"** (seccionar PostgreSQL)
4. Copia la URI, lucirá así:
   ```
   postgresql://postgres:[PASSWORD]@db.[PROJECT_ID].supabase.co:5432/postgres
   ```

📌 **Guarda esta URI, la necesitarás en Render**

---

## Fase 2: Preparación Local

### Paso 2.1: Instalar psycopg2-binary (driver PostgreSQL)
```bash
# Desde tu carpeta del proyecto con venv activado
pip install psycopg2-binary
```

### Paso 2.2: Crear script de migración de datos
Crea un archivo `migrate_to_supabase.py`:

```python
"""
Script para migrar datos de SQLite local a Supabase PostgreSQL
Uso: python migrate_to_supabase.py [DATABASE_URL]
"""

import os
import sys
import json
from datetime import datetime
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Importar modelos de la app
from app import create_app, db
from app.models.users import User, Teacher, Admin
from app.models.academic import AcademicYear, Period, Grade, Section
from app.models.grades import GradeType, StudentGrade, FinalGrade
from app.models.templates import ExcelTemplate, TemplateRow, TemplateCell

def connection_string_is_valid(conn_str):
    """Valida que la conexión sea PostgreSQL"""
    if not conn_str:
        return False
    if not conn_str.startswith('postgresql://'):
        print("❌ ERROR: Solo se acepta PostgreSQL (postgresql://...)")
        return False
    return True

def get_table_name(model):
    """Obtiene el nombre de tabla de un modelo SQLAlchemy"""
    return model.__tablename__

def migrate_data(source_db_url, target_db_url):
    """Migra datos de SQLite a PostgreSQL"""
    
    print("\n" + "="*60)
    print("🔄 INICIANDO MIGRACIÓN DE DATOS")
    print("="*60)
    
    # Conectar a base de datos local (SQLite)
    local_engine = create_engine(source_db_url, echo=False)
    
    # Conectar a Supabase (PostgreSQL)
    remote_engine = create_engine(
        target_db_url, 
        echo=False,
        poolclass=NullPool  # Evitar problemas de conexión
    )
    
    LocalSession = sessionmaker(bind=local_engine)
    RemoteSession = sessionmaker(bind=remote_engine)
    
    local_session = LocalSession()
    remote_session = RemoteSession()
    
    try:
        # 1. Verificar conexión a Supabase
        print("\n✓ Verificando conexión a Supabase...")
        with remote_engine.connect() as conn:
            result = conn.execute("SELECT version()").scalar()
            print(f"  PostgreSQL detectado: {result[:50]}...")
        
        # 2. Crear tablas en Supabase (solo si no existen)
        print("\n✓ Creando esquema en Supabase...")
        with remote_engine.begin() as conn:
            db.metadata.create_all(bind=conn)
        print("  ✓ Esquema creado/verificado")
        
        # 3. Listar modelos a migrar
        models_to_migrate = [
            User, Teacher, Admin,
            AcademicYear, Period, Grade, Section,
            GradeType, StudentGrade, FinalGrade,
            ExcelTemplate, TemplateRow, TemplateCell
        ]
        
        # 4. Migrar datos tabla por tabla
        total_records = 0
        
        for model in models_to_migrate:
            table_name = get_table_name(model)
            print(f"\n📋 Migrando tabla: {table_name}...")
            
            # Contar registros en local
            count = local_session.query(model).count()
            
            if count == 0:
                print(f"  ⊘ Sin datos para migrar")
                continue
            
            # Limpiar tabla destinode (excepto datos críticos)
            if table_name not in ['users']:  # Proteger tabla de usuarios
                try:
                    remote_session.query(model).delete()
                except Exception as e:
                    print(f"  ⚠ Aviso: No se pudo limpiar tabla anterior: {e}")
            
            # Obtener todos los registros
            records = local_session.query(model).all()
            
            # Insertar en remoto
            for record in records:
                # Detach from local session y merge en remoto
                remote_session.merge(record)
            
            # Commit cada tabla
            remote_session.commit()
            print(f"  ✓ {count} registros migrados")
            total_records += count
        
        print("\n" + "="*60)
        print(f"✅ MIGRACIÓN COMPLETADA")
        print(f"   Total de registros migrados: {total_records}")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR durante migración: {e}")
        remote_session.rollback()
        return False
        
    finally:
        local_session.close()
        remote_session.close()
        local_engine.dispose()
        remote_engine.dispose()

def main():
    # Obtener DATABASE_URL desde argumento o .env
    if len(sys.argv) > 1:
        target_db_url = sys.argv[1]
    else:
        target_db_url = os.getenv('SUPABASE_DATABASE_URL')
    
    if not target_db_url or not connection_string_is_valid(target_db_url):
        print("\n❌ ERROR: DATABASE_URL no válida")
        print("\nUso:")
        print("  python migrate_to_supabase.py 'postgresql://user:pass@host/db'")
        print("\nO establece SUPABASE_DATABASE_URL en tu entorno")
        sys.exit(1)
    
    # Database local (SQLite)
    if os.getenv('FLASK_ENV') == 'production':
        print("❌ ERROR: No ejecutar este script en producción")
        sys.exit(1)
    
    source_db_url = 'sqlite:///instance/app.db'
    
    success = migrate_data(source_db_url, target_db_url)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
```

### Paso 2.3: Crear un archivo `.env` local para testing (OPCIONAL)
```bash
# .env (no subir a git)
FLASK_ENV=development
DATABASE_URL=sqlite:///instance/app.db
SUPABASE_DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_ID].supabase.co:5432/postgres
```

---

## Fase 3: Ejecución de Migración

### Paso 3.1: Ejecutar migración de datos
```bash
# Activar venv
.\venv\Scripts\Activate.ps1

# Opción A: Usar variable de entorno
$env:SUPABASE_DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT_ID].supabase.co:5432/postgres"
python migrate_to_supabase.py

# Opción B: Pasar como argumento directo
python migrate_to_supabase.py "postgresql://postgres:[PASSWORD]@db.[PROJECT_ID].supabase.co:5432/postgres"
```

**Salida esperada:**
```
============================================================
🔄 INICIANDO MIGRACIÓN DE DATOS
============================================================

✓ Verificando conexión a Supabase...
  PostgreSQL detectado: PostgreSQL 15.1...

✓ Creando esquema en Supabase...
  ✓ Esquema creado/verificado

📋 Migrando tabla: user...
  ✓ 4 registros migrados

📋 Migrando tabla: teacher...
  ✓ 6 registros migrados

... (más tablas) ...

============================================================
✅ MIGRACIÓN COMPLETADA
   Total de registros migrados: 385
============================================================
```

### Paso 3.2: Verificar datos en Supabase
1. En dashboard de Supabase → **Table Editor**
2. Selecciona una tabla (ej: `teacher`)
3. Verifica que los registros aparezcan ✓

---

## Fase 4: Configuración de Render

### Paso 4.1: Actualizar DATABASE_URL en Render
1. Ve a tu app en Render (https://dashboard.render.com)
2. Selecciona tu servicio
3. Ve a **Settings**
4. Busca **Environment Variables**
5. Modifica `DATABASE_URL`:
   ```
   postgresql://postgres:[PASSWORD]@db.[PROJECT_ID].supabase.co:5432/postgres
   ```
6. Haz clic en **Save**

⏳ Render iniciará un nuevo deploy automáticamente

### Paso 4.2: Crear tablas en Supabase vía Render
```bash
# Opcionalmente, ejecutar migración en Render
# (si no se ejecutó via script local)

# Render Shell (si tienes acceso):
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Paso 4.3: Verificar que Render conecta a Supabase
1. En Render, ve a **Logs**
2. Deberías ver:
   ```
   SQLAlchemy database connected to postgresql://...
   ```

---

## Fase 5: Cambios en Código

### Paso 5.1: Actualizar `config.py` si es necesario
```python
import os

class Config:
    """Configuración base"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEMO_MODE = os.getenv('DEMO_MODE', 'False') == 'True'

class DevelopmentConfig(Config):
    """Desarrollo local"""
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///instance/app.db'
    )
    DEBUG = True

class ProductionConfig(Config):
    """Producción (Render + Supabase)"""
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    DEBUG = False
    DEMO_MODE = True  # Deshabilitar login en Render
```

### Paso 5.2: Verificar que `run.py` esté correcto
```python
if __name__ == '__main__':
    app = create_app()
    # La configuración se carga automáticamente según FLASK_ENV
    app.run(debug=app.config.get('DEBUG', False))
```

---

## Fase 6: Validación Post-Migración

### Paso 6.1: Checklist de verificación
- [ ] Supabase project creado
- [ ] DATABASE_URL copiada
- [ ] Datos migrados exitosamente (385+ registros)
- [ ] Render variable DATABASE_URL actualizado
- [ ] Render ejecutó nuevo deploy
- [ ] Logs de Render muestran conexión exitosa
- [ ] Dashboard en Render carga sin errores
- [ ] Paginación funciona (estudiantes, asignaciones, evaluaciones)
- [ ] Datos aparecen en reportes

### Paso 6.2: Testing en Render
1. Ve a tu URL de Render
2. Accede a `/admin/dashboard`
3. Deberías ver:
   - 6 Profesores
   - 180 Estudiantes
   - Datos en 3 períodos
4. Haz clic en **Students** → Verifica paginación
5. Haz clic en **Assignments** → Verifica paginación
6. Haz clic en **Evaluations** → Verifica paginación

---

## Troubleshooting

### Error: "connection refused"
```
SOLUCIÓN:
- Verifica que la DATABASE_URL sea correcta
- Asegúrate que Supabase project esté activo
- Espera 5 minutos después de crear el proyecto
```

### Error: "authentication failed"
```
SOLUCIÓN:
- Verifica que [PASSWORD] sea correcto (la que estableciste)
- Cópiala nuevamente desde Supabase Settings
- Escápala si tiene caracteres especiales
```

### Error: "relation does not exist"
```
SOLUCIÓN:
- Ejecuta db.create_all() en Render shell:
  python -c "from app import create_app, db; app.app_context().push(); db.create_all()"
- O re-ejecuta: python migrate_to_supabase.py
```

### Error: "too many connections"
```
SOLUCIÓN:
- SQLAlchemy poolclass mal configurado
- En config.py agregaPooling:
  SQLALCHEMY_ENGINE_OPTIONS = {
      'poolclass': NullPool,
      'pool_pre_ping': True
  }
```

---

## Resumen Ejecutivo

| Paso | Acción | Tiempo |
|------|--------|--------|
| 1 | Crear proyecto en Supabase | 3 min |
| 2 | Copiar DATABASE_URL | 1 min |
| 3 | Ejecutar migración local | 2 min |
| 4 | Actualizar DATABASE_URL en Render | 1 min |
| 5 | Esperar deploy de Render | 3 min |
| 6 | Verificar en Render | 2 min |
| **TOTAL** | | **~12 minutos** |

---

## Siguientes Pasos (Opcional)

### Hacer respaldo de Supabase
```sql
-- En Supabase SQL Editor
pg_dump -F c -d postgres > backup.sql
```

### Monitoreo
- Dashboard Supabase → **Usage**
- Render → **Logs** cada semana

### Escalabilidad
Si necesitas más almacenamiento/conexiones:
- Supabase Free → Supabase Pro ($25/mes)
- Render Free → Render Starter ($7/mes)
