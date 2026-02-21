# 🚀 Guía de Despliegue: Demo en Render + Neon.tech + UptimeRobot

Esta guía te explica cómo desplegar el sistema en modo **DEMO** (acceso público sin login) con:
- **Neon.tech**: Base de datos PostgreSQL permanente (gratuito)
- **Render**: Hosting para la aplicación Flask (gratuito)
- **UptimeRobot**: Mantiene el servidor activo

---

## **📋 Paso 1: Preparar el proyecto localmente**

### 1.1 Instalar dependencias
```bash
pip install -r requirements.txt
```

### 1.2 Crear la base de datos local (SQLite)
```bash
flask db upgrade
```

### 1.3 Poblar con datos de demostración
```bash
python seed_demo_data.py
```

Deberías ver:
```
✅ ¡Base de datos poblada exitosamente!
  📊 4 Grados
  📚 12 Secciones
  👨‍🏫 4 Profesores
  👨‍🎓 156 Estudiantes
  📝 6 Asignaturas
```

### 1.4 Probar localmente en DEMO MODE
```bash
# En tu terminal
export DEMO_MODE=true
python run.py
```

Luego abre: `http://localhost:5000`

Debería entrar directo al dashboard sin pedir login ✅

---

## **☁️ Paso 2: Configurar Base de Datos en Neon.tech**

### 2.1 Crear cuenta en Neon
1. Ir a [https://neon.tech](https://neon.tech)
2. Hacer clic en **"Sign Up"**
3. Registrarse con GitHub (recomendado) o email
4. Confirmar email

### 2.2 Crear proyecto
1. Haz clic en **"New Project"**
2. Dale un nombre: `gestor-calificaciones-demo`
3. Selecciona región más cercana a ti
4. Haz clic en **"Create"**

### 2.3 Obtener la conexión string
Después de crear el proyecto:
1. Haz clic en tu proyecto
2. En la sección **"Connection string"**, selecciona **"Pooled connection"**
3. Copia la URL completa (empieza con `postgresql://`)

Ejemplo:
```
postgresql://neondb_owner:abc123@ep-cool-dust.us-east-1.neon.tech/neondb?sslmode=require
```

**Guarda esta URL** - la necesitarás para Render.

---

## **🚀 Paso 3: Desplegar en Render**

### 3.1 Crear cuenta en Render
1. Ir a [https://render.com](https://render.com)
2. Haz clic en **"Sign up"**
3. Conecta tu GitHub

### 3.2 Crear Web Service
1. En el dashboard, haz clic en **"New +"** → **"Web Service"**
2. Selecciona tu repositorio `gestor-calificaciones`
3. Llena los campos:

| Campo | Valor |
|-------|-------|
| **Name** | `gestor-calificaciones-demo` |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && flask db upgrade` |
| **Start Command** | `gunicorn run:app` |
| **Instance Type** | Free (gratuito) |

### 3.3 Configurar variables de entorno
Haz clic en **"Environment"** y agrega:

```
FLASK_ENV=production
SECRET_KEY=change-this-to-random-string-abc123xyz789
DATABASE_URL=<paste-neon-url-here>
DEMO_MODE=true
LOG_TO_STDOUT=true
```

**Importante**: Para `SECRET_KEY`, genera una cadena aleatoria:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3.4 Desplegar
Haz clic en **"Create Web Service"**

Render comenzará a desplegar. Espera 3-5 minutos.

Deberías ver un URL como: `https://gestor-calificaciones-demo.onrender.com`

---

## **🔄 Paso 4: Ejecutar migraciones en Render**

Una vez que Render haya construido la aplicación:

### 4.1 Acceder a Render Shell
1. En tu servicio de Render, haz clic en **"Shell"**
2. Ejecuta:

```bash
flask db upgrade
python seed_demo_data.py
```

Deberías ver el mensaje de éxito:
```
✅ ¡Base de datos poblada exitosamente!
```

---

## **🤖 Paso 5: Mantener el servidor activo con UptimeRobot**

Como Render tiene instancias gratuitas que se hibernan después de 15 min sin tráfico, usaremos UptimeRobot para "despertar" el servidor regularmente.

### 5.1 Crear cuenta en UptimeRobot
1. Ir a [https://uptimerobot.com](https://uptimerobot.com)
2. Haz clic en **"Sign Up"** (es gratis)
3. Confirma tu email

### 5.2 Crear Monitor
1. En el dashboard, haz clic en **"Add New Monitor"**
2. Rellena:

| Campo | Valor |
|-------|-------|
| **Monitor Type** | HTTP(s) |
| **Friendly Name** | Gestor Calificaciones Demo |
| **URL** | `https://gestor-calificaciones-demo.onrender.com` |
| **Monitoring Interval** | 5 minutes |

3. Haz clic en **"Create Monitor"**

¡Listo! UptimeRobot visitará tu sitio cada 5 minutos, manteniéndolo activo.

---

## **✅ Verificar que todo funciona**

1. Abre: `https://gestor-calificaciones-demo.onrender.com`
2. Deberías ver el **dashboard de admin** inmediatamente
3. Puedes ver:
   - **Estudiantes**: ~156 estudiantes
   - **Profesores**: 4 profesores
   - **Asignaturas**: 6 materias
   - **Grados**: 4 grados

---

## **📊 Monitoreo y Logs**

### Ver logs en Render
En el dashboard de Render, haz clic en **"Logs"** para ver errores.

### Revisar estado en UptimeRobot
En el dashboard de UptimeRobot, verás el estado de tu monitor:
- 🟢 **Up**: El servidor está respondiendo
- 🔴 **Down**: Hay un problema

---

## **🔧 Problemas comunes**

### "Module not found"
**Solución**: Asegúrate de que `requirements.txt` está actualizado:
```bash
pip freeze > requirements.txt
```

### "Database connection error"
**Solución**: 
1. Verifica la URL de Neon en las variables de Render
2. Asegúrate de que `DATABASE_URL` contiene `?sslmode=require`

### "No data in dashboard"
**Solución**:
1. En Render Shell, ejecuta de nuevo:
```bash
python seed_demo_data.py
```

---

## **📝 Variables de entorno finales en Render**

```env
FLASK_ENV=production
SECRET_KEY=tu-secret-key-aleatorio
DATABASE_URL=postgresql://...neon.tech/...
DEMO_MODE=true
LOG_TO_STDOUT=true
```

---

## **✨ Resultado final**

Ahora tienes:
- ✅ App funcionando en `https://gestor-calificaciones-demo.onrender.com`
- ✅ BD persistente en Neon.tech
- ✅ Acceso público sin login (DEMO_MODE=true)
- ✅ Servidor siempre activo (UptimeRobot)
- ✅ Datos ficticios pre-cargados

¡Listo para tu portafolio! 🎉

