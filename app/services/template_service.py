from openpyxl import load_workbook
from app.models.templates import ExcelTemplate, TemplateCell, TemplateStyle
from app.services.template_mapper import TemplateMapper
from app import db
import json
import os
import re

class TemplateService:
    
    @staticmethod
    def analyze_template_structure(template_id, file_path):
        """Analiza la estructura de un archivo Excel y detecta tipos de datos automáticamente"""
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        try:
            wb = load_workbook(file_path)
            ws = wb.active
            
            # Limpiar datos existentes
            TemplateCell.query.filter_by(template_id=template_id).delete()
            TemplateStyle.query.filter_by(template_id=template_id).delete()
            
            # Analizar por columnas para detectar patrones
            column_data = {}
            
            # Recopilar datos de cada columna
            for col_num in range(1, ws.max_column + 1):
                col_letter = ws.cell(row=1, column=col_num).column_letter
                column_data[col_letter] = []
                
                # Tomar las primeras 5 filas como muestra
                for row_num in range(1, min(6, ws.max_row + 1)):
                    cell = ws.cell(row=row_num, column=col_num)
                    if cell.value:
                        column_data[col_letter].append(cell.value)
            
            # Detectar tipo de cada columna
            column_types = {}
            for col_letter, values in column_data.items():
                column_types[col_letter] = TemplateMapper.detect_column_type(col_letter, values)
            
            # Crear registros de celdas
            for row in ws.iter_rows():
                for cell in row:
                    if cell.value is not None:
                        col_letter = cell.column_letter
                        data_type = column_types.get(col_letter, 'static')
                        
                        template_cell = TemplateCell(
                            template_id=template_id,
                            cell_address=cell.coordinate,
                            cell_type='data' if data_type != 'static' else 'static',
                            data_type=data_type,
                            default_value=str(cell.value),
                            style_config=TemplateService._extract_cell_style(cell)
                        )
                        db.session.add(template_cell)
            
            # Guardar estilos de columnas
            for col_letter, col_dimension in ws.column_dimensions.items():
                if col_dimension.width:
                    template_style = TemplateStyle(
                        template_id=template_id,
                        range_address=f"{col_letter}:{col_letter}",
                        column_width=col_dimension.width
                    )
                    db.session.add(template_style)
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al analizar plantilla: {str(e)}")
    
    @staticmethod
    def _extract_cell_style(cell):
        """Extrae los estilos de una celda"""
        style_config = {}
        
        if cell.font:
            style_config['font'] = {
                'name': cell.font.name or 'Arial',
                'size': cell.font.size or 11,
                'bold': cell.font.bold or False,
                'italic': cell.font.italic or False
            }
        
        if cell.fill and cell.fill.start_color:
            style_config['fill'] = {
                'color': str(cell.fill.start_color.rgb) if cell.fill.start_color.rgb else 'FFFFFF'
            }
        
        if cell.alignment:
            style_config['alignment'] = {
                'horizontal': cell.alignment.horizontal or 'left',
                'vertical': cell.alignment.vertical or 'top'
            }
        
        return json.dumps(style_config) if style_config else None
    
    @staticmethod
    def generate_preview(template_id):
        """Genera vista previa mostrando qué tipo de dato va en cada celda"""
        
        template = ExcelTemplate.query.get_or_404(template_id)
        cells = TemplateCell.query.filter_by(template_id=template_id).all()
        
        preview_data = {}
        for cell in cells:
            row_num = int(re.search(r'\d+', cell.cell_address).group())
            col_letter = re.search(r'[A-Z]+', cell.cell_address).group()
            
            if row_num not in preview_data:
                preview_data[row_num] = {}
            
            # Mostrar el tipo de dato que se inyectará
            if cell.cell_type == 'data':
                display_value = f"[{cell.data_type.upper()}]"
            else:
                display_value = cell.default_value
            
            preview_data[row_num][col_letter] = {
                'value': display_value,
                'type': cell.data_type,
                'original': cell.default_value
            }
        
        return preview_data

# Agregar estos métodos al final de la clase TemplateService

@staticmethod
def generate_preview_with_config(template_id, config_data, sample_data):
    """Genera vista previa basada en configuración"""
    
    try:
        template = ExcelTemplate.query.get_or_404(template_id)
        preview_data = {}
        
        # Procesar celdas individuales
        if 'individual_cells' in config_data:
            for cell_config in config_data['individual_cells']:
                address = cell_config['address']
                data_type = cell_config['data_type']
                custom_text = cell_config.get('custom_text', '')
                
                # Extraer fila y columna
                row_num = int(''.join(filter(str.isdigit, address)))
                col_letter = ''.join(filter(str.isalpha, address))
                
                if row_num not in preview_data:
                    preview_data[row_num] = {}
                
                # Generar valor según el tipo
                value = TemplateService._get_preview_value(data_type, sample_data, custom_text)
                
                preview_data[row_num][col_letter] = {
                    'value': value,
                    'type': data_type
                }
        
        # Procesar rangos iterativos
        if 'ranges' in config_data:
            for range_config in config_data['ranges']:
                start_cell = range_config['start_cell']
                mapping = range_config['mapping']
                range_type = range_config['type']
                
                # Extraer posición inicial
                start_row = int(''.join(filter(str.isdigit, start_cell)))
                start_col_letter = ''.join(filter(str.isalpha, start_cell))
                start_col_num = ord(start_col_letter) - ord('A')
                
                # Obtener datos según el tipo de rango
                data_list = TemplateService._get_range_data(range_type, sample_data)
                
                # Llenar el rango
                for row_offset, item_data in enumerate(data_list[:10]):  # Máximo 10 filas en preview
                    current_row = start_row + row_offset
                    
                    if current_row not in preview_data:
                        preview_data[current_row] = {}
                    
                    for col_offset, (col_key, data_key) in enumerate(mapping.items()):
                        current_col_num = start_col_num + col_offset
                        current_col_letter = chr(ord('A') + current_col_num)
                        
                        value = TemplateService._get_item_value(item_data, data_key, row_offset)
                        
                        preview_data[current_row][current_col_letter] = {
                            'value': value,
                            'type': data_key
                        }
        
        return preview_data
        
    except Exception as e:
        print(f"Error en generate_preview_with_config: {str(e)}")
        raise e

@staticmethod
def _get_preview_value(data_type, sample_data, custom_text=''):
    """Obtiene valor de vista previa para un tipo de dato"""
    
    if data_type == 'custom_text' and custom_text:
        return custom_text
    
    preview_values = {
        'static': 'Texto estático',
        'custom_text': custom_text or 'Texto personalizado',
        'titulo_reporte': 'REPORTE DE CALIFICACIONES',
        'nombre_institucion': 'U.E. MI INSTITUCIÓN',
        'seccion': sample_data.get('section', {}).get('name', '1ro "A"'),
        'grado': sample_data.get('section', {}).get('grade', {}).get('name', '1er Año'),
        'periodo': sample_data.get('period', {}).get('name', '1er Lapso'),
        'fecha_actual': sample_data.get('current_date', '13/06/2025'),
        'total_estudiantes': f"{len(sample_data.get('students', []))} estudiantes",
        'promedio_seccion': '16.8',
        'estudiantes_aprobados': '22 aprobados',
        'estudiantes_reprobados': '3 reprobados'
    }
    
    return preview_values.get(data_type, f'[{data_type}]')

@staticmethod
def _get_range_data(range_type, sample_data):
    """Obtiene datos para un tipo de rango"""
    
    if range_type == 'students':
        return sample_data.get('students', [])
    elif range_type == 'subjects':
        return sample_data.get('subjects', [])
    elif range_type == 'grades_by_student':
        students = sample_data.get('students', [])
        # Agregar notas de ejemplo
        for i, student in enumerate(students):
            student['materia_1'] = 18.5 - i
            student['materia_2'] = 17.0 + i * 0.5
            student['materia_3'] = 16.8 + i * 0.3
            student['promedio'] = (student['materia_1'] + student['materia_2'] + student['materia_3']) / 3
        return students
    
    return []

@staticmethod
def _get_item_value(item_data, data_key, index):
    """Obtiene valor específico de un item"""
    
    if data_key == 'numero':
        return str(index + 1)
    elif data_key in item_data:
        return str(item_data[data_key])
    else:
        return f'[{data_key}]'

@staticmethod
def generate_preview_excel(template_id):
    """Genera Excel de vista previa"""
    
    from openpyxl import Workbook
    
    # Por ahora retornamos un workbook básico
    wb = Workbook()
    ws = wb.active
    ws.title = "Vista Previa"
    
    ws['A1'] = "Vista previa de plantilla"
    ws['A2'] = "Funcionalidad en desarrollo"
    
    return wb
