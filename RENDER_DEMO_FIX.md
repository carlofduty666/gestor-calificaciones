# Solucionar "relation users does not exist" en Render

## Problema
Cuando accedes a `https://smartboletin-demo.onrender.com/`, ves el error:
```
relation "users" does not exist
```

## Causa Raíz
**Las migraciones de la base de datos NO se han aplicado en Neon.tech**. Esto significa que:
- Las tablas SQL no existen
- No hay tabla `users`
- No hay tabla `academic_years`, `grades`, etc.

## Solución Rápida (RECOMENDADO)

### Paso 1: Abre Render Shell
1. Ve a https://dashboard.render.com/
2. Selecciona tu servicio: `smartboletin-demo`
3. Ve a la pestaña: **"Shell"**

### Paso 2: Ejecuta el Script de Inicialización
En la shell, ejecuta:
```bash
python setup_remote_db.py
```

### Paso 3: Espera a que Termine
Deberías ver algo como:
```
==========================================================================================
INICIALIZADOR COMPLETO DE BASE DE DATOS REMOTA PARA RENDER
==========================================================================================

[OK] Base de datos detectada: postgresql://...

[PASO 1/3] Aplicando migraciones (creando tablas)...
[OK] Migraciones aplicadas exitosamente

[PASO 2/3] Verificando conexión a la base de datos...
[OK] Conexión a base de datos exitosa

[PASO 3/3] Creando/verificando usuario demo...
   → Usuario demo NO existe, creando...
   [OK] Usuario demo creado

[INFORMACIÓN FINAL] Usuario demo:
   ├─ Email: demo@example.com
   ├─ Nombre: Demo Admin
   ├─ Rol: admin
   ├─ Activo: True
   ├─ Registrado: True
   └─ is_admin(): True

==========================================================================================
COMPLETADO - Base de datos remota inicializada correctamente!
==========================================================================================

Proximos pasos:
1. Vuelve a Render Dashboard
2. Ve a tu servicio y espera que termine de redeploy
3. Accede a: https://smartboletin-demo.onrender.com/
```

### Paso 4: Accede a tu Sitio
Abre tu navegador y ve a:
```
https://smartboletin-demo.onrender.com/
```

**¡Debería funcionar ahora!** ✅

## Alternativa Manual (Si Shell no funciona)

Si no tienes acceso a la shell o prefieres hacer paso a paso:

### Opción A: Aplicar migraciones solo
```bash
flask db upgrade
```

### Opción B: Crear usuario demo solo
```bash
python ensure_demo_user.py
```

### Opción C: Hacer todo
```bash
flask db upgrade
python ensure_demo_user.py
```

## Credenciales Demo Finales
```
Email: demo@example.com
Contraseña: demo123
Rol: admin
```

## Validación Si Algo Falla

### Para ver qué pasó, revisa los logs:
1. Dashboard.render.com → Tu servicio → "Logs"
2. Busca errores como:
   - `relation "users" does not exist` → Las migraciones no se aplicaron
   - `ProgrammingError` → Problemas con SQL
   - `connection refused` → Problema de conexión a BD

### Para verificar que TODO está correcto:
1. Abre Shell en Render
2. Ejecuta:
   ```bash
   python diagnose.py
   ```
3. Deberías ver:
   ```
   USUARIO DEMO ENCONTRADO:
   Role: admin
   is_admin(): True
   ```

## Si Aún Hay Problemas

### Opción 1: Reset Completo de BD en Neon
1. Ve a https://console.neon.tech
2. Selecciona tu base de datos
3. SQL Editor → Ejecuta:
   ```sql
   DROP SCHEMA public CASCADE;
   CREATE SCHEMA public;
   ```
4. Luego ejecuta `python setup_remote_db.py` de nuevo

### Opción 2: Resetear Render (Nuclear Option)
1. En Render Dashboard → Tu servicio → Settings
2. Scroll abajo → "Delete Service"
3. Crea el servicio de nuevo

## Resumen de lo que hace `setup_remote_db.py`

El script hace TRES cosas en orden:

```
1. Conecta a la BD en Neon.tech
2. Ejecuta: flask db upgrade
   → Crea tabla 'users'
   → Crea tabla 'academic_years'
   → Crea tabla 'grades'
   → Crea tabla 'sections'
   → Crea todas las demás tablas
3. Crea el usuario demo en la tabla 'users'
```

## Variables de Entorno Requeridas en Render

Verifica que estén configuradas en tu servicio:
- ✅ `DATABASE_URL` - Tu URL de Neon.tech
- ✅ `DEMO_MODE` - `true`
- ✅ `FLASK_ENV` - `production`
- ✅ `SECRET_KEY` - Una clave aleatoria

## Próximos Pasos

1. ✅ Abre Render Shell
2. ✅ Ejecuta `python setup_remote_db.py`
3. ✅ Espera a que termine (5-10 segundos)
4. ✅ Accede a tu sitio
5. ✅ ¡Disfruta!

---

**¿Todavía tiene problemas?** Revisa los logs en Render Dashboard → Tu servicio → "Logs"

