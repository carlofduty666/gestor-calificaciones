# Solucionar "Error en Modo Demo" en Render

## Problema
Cuando accedes a `https://smartboletin-demo.onrender.com/`, ves el mensaje:
```
Error en modo demo
```

## Causa
La base de datos en Neon.tech no tiene el usuario `demo@example.com` creado.

## Solución Rápida (RECOMENDADO)

### Opción 1: Usar la Shell de Render (Más fácil)

1. Abre tu panel en https://dashboard.render.com/
2. Selecciona tu servicio (smartboletin-demo)
3. Ve a la pestaña **"Shell"**
4. En la shell, ejecuta:
   ```bash
   python ensure_demo_user.py
   ```
5. Deberías ver algo como:
   ```
   ================================================================================
   VERIFICANDO/CREANDO USUARIO DEMO
   ================================================================================
   
   [OK] Usuario demo creado exitosamente
   ...
   COMPLETADO - Usuario demo listo para usar
   ```

6. Una vez hecho, accede a tu sitio: `https://smartboletin-demo.onrender.com/`

### Opción 2: Script Remoto (Si la Shell no funciona)

Si no tienes acceso a la shell, ejecuta este script desde tu máquina local:

```bash
# 1. Asegúrate de tener las variables de entorno
export DATABASE_URL="postgresql://user:pass@ep-...neon.tech/neondb"
export DEMO_MODE=true

# 2. Ejecuta el script
python init_remote_db.py
```

## ¿Qué Ocurre Automáticamente Ahora?

Hemos mejorado el código para que:

1. **Si el usuario demo NO existe**, la aplicación lo crea automáticamente cuando:
   - Accedes a `/` (ruta raíz)
   - Accedes a `/auth/login`

2. **Si el usuario demo EXISTE pero tiene rol incorrecto**, se corrige automáticamente

3. **Si hay error al conectar a la BD**, se muestra un mensaje descriptivo en lugar de "Error en modo demo"

## Verificación

Después de ejecutar `python ensure_demo_user.py`, deberías ver:

```
[FINAL] Estado del usuario demo:
   ID: 1
   Email: demo@example.com
   Nombre: Demo Admin
   Rol: admin
   Activo: True
   Registrado: True
   is_admin(): True
```

## Logeo Manual (Si nada funciona)

Credentials finales:
- Email: `demo@example.com`
- Contraseña: `demo123`

Accede a: `https://smartboletin-demo.onrender.com/auth/login`

## Logs para Debugging

Si aún tienes problemas:

1. Ve a tu servicio en Render
2. Pestaña **"Logs"**
3. Busca errores que comiencen con:
   - `[ERROR]`
   - `Error en login automático DEMO`
   - `DatabaseError`

4. Comparte el error exacto para más ayuda

## Variables de Entorno en Render

Verifica que tu servicio tenga configuradas:

```
DATABASE_URL = postgresql://...  (Tu URL de Neon)
DEMO_MODE = true
FLASK_ENV = production (o development)
SECRET_KEY = tu_clave_secreta
```

## Próximos Pasos

1. ✅ Ejecuta `python ensure_demo_user.py` en Render Shell
2. ✅ Accede a `https://smartboletin-demo.onrender.com/`
3. ✅ Deberías ver el dashboard de admin

¡Éxito!
