class TemplateMapper:
    
    # Mapeo simple de tipos de datos a valores reales
    DATA_TYPES = {
        'cedula': lambda student, context: student.student_id,
        'nombre': lambda student, context: student.first_name,
        'apellido': lambda student, context: student.last_name,
        'nombre_completo': lambda student, context: f"{student.first_name} {student.last_name}",
        'seccion': lambda student, context: context['section'].name,
        'grado': lambda student, context: context['grade'].name,
        'nota': lambda student, context: TemplateMapper._get_student_grade(student, context),
        'promedio': lambda student, context: TemplateMapper._get_student_average(student, context),
        'fecha': lambda student, context: context['current_date'],
    }
    
    @staticmethod
    def _get_student_grade(student, context):
        """Obtiene la nota del estudiante para el período actual"""
        from app.models.grades import FinalGrade
        
        grade = FinalGrade.query.filter_by(
            student_id=student.id,
            period_id=context['period_id']
        ).first()
        
        return grade.value if grade else 0
    
    @staticmethod
    def _get_student_average(student, context):
        """Obtiene el promedio del estudiante"""
        from app.models.grades import FinalGrade
        
        grades = FinalGrade.query.filter_by(
            student_id=student.id,
            period_id=context['period_id']
        ).all()
        
        if grades:
            return sum(g.value for g in grades) / len(grades)
        return 0
    
    @staticmethod
    def get_value_for_cell(data_type, student, context):
        """Obtiene el valor para una celda específica"""
        if data_type in TemplateMapper.DATA_TYPES:
            return TemplateMapper.DATA_TYPES[data_type](student, context)
        return None
    
    @staticmethod
    def detect_column_type(column_letter, sample_values):
        """Detecta automáticamente qué tipo de dato va en una columna"""
        
        # Unir todos los valores de muestra
        combined_text = ' '.join(str(v).lower() for v in sample_values if v).strip()
        
        # Patrones de detección
        if any(word in combined_text for word in ['cedula', 'ci', 'documento', 'id']):
            return 'cedula'
        elif any(word in combined_text for word in ['nombre', 'name']):
            return 'nombre'
        elif any(word in combined_text for word in ['apellido', 'surname', 'lastname']):
            return 'apellido'
        elif any(word in combined_text for word in ['nota', 'calificacion', 'grade']):
            return 'nota'
        elif any(word in combined_text for word in ['promedio', 'average']):
            return 'promedio'
        elif any(word in combined_text for word in ['seccion', 'section']):
            return 'seccion'
        elif any(word in combined_text for word in ['grado', 'grade', 'curso']):
            return 'grado'
        
        return 'static'  # Por defecto
