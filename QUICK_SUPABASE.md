# Guía Rápida: Supabase en 5 Minutos

## ⚡ Resumen Ejecutivo

**Tiempo total:** ~15 minutos  
**Costo:** $0 (plan gratuito)  
**Riesgo:** Bajo (datos locales sin cambios)

---

## 📋 Checklist Pre-Requisitos

- [ ] Ya tienes `seed_demo_data.py` ejecutado (180 estudiantes, 6 profesores)
- [ ] Base de datos local tiene datos: `instance/app.db` (>1MB)
- [ ] Venv activado: `. .\venv\Scripts\Activate.ps1`
- [ ] Ya lograste desplegar en Render sin Supabase

---

## 🚀 Pasos Rápidos

### 1️⃣ CREAR PROYECTO EN SUPABASE (3 minutos)

```
Ir a: https://supabase.com → Sign Up
├── Email: tu_email@example.com
├── Nombre proyecto: gestor-calificaciones
├── Password: PickStrong123!  ← copia esto
├── Región: us-east-1 (o la más cercana)
└── Plan: Free
```

**Espera a que diga "Project is ready" (2-3 min)** ⏳

### 2️⃣ COPIAR CONNECTION STRING (1 minuto)

```
En Supabase Dashboard:
Settings → Database → Connection Strings → URI

Copia esto (conserva [PASSWORD]):
postgresql://postgres:PickStrong123@db.abc123.supabase.co:5432/postgres
```

### 3️⃣ INSTALAR DRIVER (1 minuto)

```powershell
pip install psycopg2-binary
# O si ya lo tienes:
pip install --upgrade psycopg
```

### 4️⃣ EJECUTAR MIGRACIÓN (2 minutos)

```powershell
# En tu terminal (venv activado)
python migrate_to_supabase.py "postgresql://postgres:PickStrong123@db.abc123.supabase.co:5432/postgres"

# Verás:
# 🔄 MIGRACIÓN DE DATOS
# ✓ Usuarios......... 4
# ✓ Profesores...... 6  
# ✓ Estudiantes..... 180
# ✅ MIGRACIÓN COMPLETADA - 385 registros
```

### 5️⃣ ACTUALIZAR RENDER (2 minutos)

```
Dashboard Render → Tu servicio → Environment
├── Modificar: DATABASE_URL
├── Nuevo valor: postgresql://postgres:PickStrong123@db.abc123.supabase.co:5432/postgres
└── Guardar → Auto-redeploy ✓
```

**Espera 2-3 minutos a que Render redeploy**

### 6️⃣ VERIFICAR (1 minuto)

```
Tu URL en Render → /admin/dashboard
├── ¿Aparecen 180 estudiantes?
├── ¿Funciona paginación?
└── ¿Sin errores de conexión?
```

---

## 🔐 Formato Correcto de DATABASE_URL

**CORRECTO:**
```
postgresql://postgres:tuPassword@db.abc123xyz.supabase.co:5432/postgres
```

**INCORRECTO (errores comunes):**
```
postgres://...          ❌ (debe ser postgresql://)
postgresql://db.abc...  ❌ (falta usuario:password)
postgresql://... :5432  ❌ (falta /postgres al final)
```

---

## 🆘 Si Falla Migrate

### Error: "connection refused"
```powershell
# Espera 5 minutos más, Supabase tarda en inicializar
Start-Sleep -Seconds 300
python migrate_to_supabase.py "postgresql://..."
```

### Error: "authentication failed"
```powershell
# Verifica tu password exacto en Supabase
# Settings → Database → Username: postgres
# Si tiene @, #, $, etc., cópialo exactamente
```

### Error: "relation does not exist"
```powershell
# Las tablas no se crearon. Intenta:
# Opción A: Vuelve a ejecutar migrate_to_supabase.py
# Opción B: En Render render shell:
#   python -c "from app import db, create_app; create_app().app_context().push(); db.create_all()"
```

---

## 📊 Validación Post-Migración

### En Supabase Console:
```
Dashboard → Table Editor
├── Selecciona "teacher"
├── Deberías ver 6 profesores
└── ✓ Datos están ahí
```

### En Render Console:
```
Logs → Busca "Database:" or "postgres"
└── ✓ Debe mostrar conexión exitosa a Supabase
```

---

## 📝 Variables de Entorno

**Desarrollo Local:**
```bash
# .env (no subir a git)
FLASK_ENV=development
DATABASE_URL=sqlite:///instance/app.db
```

**Render (Production):**
```
DATABASE_URL=postgresql://postgres:xxx@db.xxx.supabase.co:5432/postgres
FLASK_ENV=production
DEMO_MODE=True
```

---

## 🎯 Próximos Pasos Opcionales

1. **Backup Automático**: Supabase → Backups (gratis, semanal)
2. **Monitoreo**: Supabase → Usage Statistics
3. **Escalabilidad**: Si superas límites free, upgrade a $25/mes

---

## 📞 Soporte Rápido

| Problema | Solución |
|----------|----------|
| Base de datos no conecta | Verifica DATABASE_URL en Render |
| Datos no aparecen | Ejecuta `migrate_to_supabase.py` nuevamente |
| Lento después de deploy | Espera 5 min, Render está inicializando conexión |
| Errores 500 en Render | Ver Logs → busca "SQLAlchemy" |

---

## ✨ Una Vez Completado

Tu app estará:
- ✅ Corriendo en Render (servidor web)
- ✅ Conectada a Supabase (PostgreSQL remoto)
- ✅ Con 180 estudiantes de demo
- ✅ Datos persistentes (no se borran al redeploy)
- ✅ Paginación funcionando en 3 vistas
- ✅ Escalable (agrega más datos sin problemas)

🎉 **¡Felicitaciones! Tu app está lista para producción**
