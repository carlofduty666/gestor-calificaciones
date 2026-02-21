# Guía de Paginación - Patrón Recomendado

## ✅ Patrón Correcto (Sintaxis Segura)

### En la Ruta (Python/Flask):
```python
@route('/estudiantes')
def students():
    page = request.args.get('page', 1, type=int)
    
    # Construir query con filtros
    query = Student.query
    if grade_id := request.args.get('grade_id'):
        query = query.filter_by(grade_id=grade_id)
    if search := request.args.get('search'):
        query = query.filter(Student.first_name.like(f'%{search}%'))
    
    # Paginar
    pagination = query.order_by(Student.last_name).paginate(
        page=page, 
        per_page=20,  # Ajusta según necesidades
        error_out=False
    )
    
    return render_template(
        'admin/students.html',
        students=pagination.items,  # Solo los items de esta página
        pagination=pagination,       # Objeto de paginación
        # ... otros datos
    )
```

### En el Template (Jinja2):
```html
<!-- Mostrar items pagados -->
{% for item in items %}
    <tr>
        <td>{{ item.name }}</td>
        <!-- ... más columnas ... -->
    </tr>
{% endfor %}

<!-- Paginación: SIEMPRE usar parámetros explícitos -->
{% if pagination and pagination.pages > 1 %}
<nav aria-label="Navegación de páginas" class="mt-4">
    <ul class="pagination justify-content-center">
        {% if pagination.has_prev %}
        <li class="page-item">
            <a class="page-link" href="{{ url_for('ruta', 
                page=pagination.prev_num,
                param1=request.args.get('param1'),
                param2=request.args.get('param2')
            ) }}" aria-label="Anterior">
                <span aria-hidden="true">&laquo;</span>
            </a>
        </li>
        {% endif %}
        
        {% for page_num in pagination.iter_pages(left_edge=2, left_current=2, right_current=3, right_edge=2) %}
            {% if page_num %}
                {% if page_num == pagination.page %}
                <li class="page-item active">
                    <a class="page-link" href="#">{{ page_num }}</a>
                </li>
                {% else %}
                <li class="page-item">
                    <a class="page-link" href="{{ url_for('ruta',
                        page=page_num,
                        param1=request.args.get('param1'),
                        param2=request.args.get('param2')
                    ) }}">{{ page_num }}</a>
                </li>
                {% endif %}
            {% else %}
            <li class="page-item disabled">
                <a class="page-link" href="#">...</a>
            </li>
            {% endif %}
        {% endfor %}
        
        {% if pagination.has_next %}
        <li class="page-item">
            <a class="page-link" href="{{ url_for('ruta',
                page=pagination.next_num,
                param1=request.args.get('param1'),
                param2=request.args.get('param2')
            ) }}" aria-label="Siguiente">
                <span aria-hidden="true">&raquo;</span>
            </a>
        </li>
        {% endif %}
    </ul>
</nav>
{% endif %}
```

## ❌ Patrón INCORRECTO (Causa errores)

### Error 1: Jinja2 Dict Comprehension
```jinja2
{# ESTO NO FUNCIONA en Jinja2 #}
{% set args_without_page = dict((k, v) for k, v in request.args.items() if k != 'page') %}
{{ url_for('admin.students', page=1, **args_without_page) }}
```

**Error:** `TemplateSyntaxError: expected token ',', got 'for'`

### Error 2: Desempaquetamiento de request.args
```jinja2
{# ESTO CAUSA CONFLICTO DE PARÁMETROS #}
{{ url_for('admin.students', page=2, **request.args) }}
```

**Error:** `TypeError: url_for() got multiple values for keyword argument 'page'`

## ✅ Casos de Uso Correctamente Implementados

| Template | Ruta | Elementos/Página | Filtros |
|----------|------|------------------|---------|
| admin/students.html | admin.students | 20 | grade_id, section_id, search |
| admin/assignments.html | admin.assignments | 20 | academic_year, teacher, subject, section |
| admin/grade_types.html | admin.evaluations | 15 | subject_id, period_id, grade_id, section_id |

## 📋 Checklist para Agregar Paginación a un Template Nuevo

- [ ] **Ruta (Python):**
  - [ ] Leer `page = request.args.get('page', 1, type=int)`
  - [ ] Usar `.paginate(page=page, per_page=N, error_out=False)`
  - [ ] Pasar `pagination=pagination` al template
  - [ ] Pasar `items=pagination.items` (no todos los items)

- [ ] **Template (Jinja2):**
  - [ ] Iterar sobre `{% for item in items %}`
  - [ ] Agregar bloque de paginación SOLO si `{% if pagination and pagination.pages > 1 %}`
  - [ ] **OBLIGATORIO:** Usar parámetros explícitos en `url_for()`:
    ```jinja2
    url_for('ruta', page=numero, param1=request.args.get('param1'), ...)
    ```
  - [ ] NO usar `**request.args` nunca
  - [ ] NO usar dict comprehensions en Jinja2

## 🔒 Configuraciones Recomendadas por Tipo de Vista

### Listas administrativas (Tablas grandes)
```python
pagination = query.paginate(page=page, per_page=20, error_out=False)
```

### Evaluaciones/Calificaciones (Menos items, más datos por item)
```python
pagination = query.paginate(page=page, per_page=15, error_out=False)
```

### Reportes (Datos de solo lectura)
```python
pagination = query.paginate(page=page, per_page=25, error_out=False)
```

## 📌 Notas Importantes

1. **Siempre usar `error_out=False`** para que no lance 404 si la página no existe - mejor devuelve última página
2. **Parámetros dinámicos:** Si tienes filtros, SIEMPRE pasarlos explícitamente en cada link de paginación
3. **Variable de loop:** Usar `page_num` en lugar de `page` en loops para evitar conflictos con `pagination.page`
4. **Objeto pagination:** Tiene propiedades útiles como `pagination.pages`, `pagination.has_prev`, `pagination.has_next`, `pagination.iter_pages()`

## 🚀 Próximos Candidatos para Paginación

Si los datos crecen, considera agregar paginación a:

1. **teacher/view_grades.html** - Ruta `teacher.view_grades`
   - Actualmente carga todos los estudiantes de una sección
   - Recomendado: 25 estudiantes/página

2. **teacher/enter_final_grades.html** - Ruta `teacher.enter_final_grades`
   - **NOTA:** Este es un formulario POST, paginación es más compleja
   - Considerar: JS dinámico o multi-step form

3. **reports/section_report.html** - Reportes
   - Puede tener muchos datos
   - Evaluar si necesita paginación basada en tamaño del reporte
