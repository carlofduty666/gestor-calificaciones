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
        """Analiza la estructura de un archivo Excel y crea celdas automáticamente"""
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        try:
            # Cargar workbook
            wb = load_workbook(file_path)
            ws = wb.active
            
            # Limpiar celdas existentes
            TemplateCell.query.filter_by(template_id=template_id).delete()
            TemplateStyle.query.filter_by(template_id=template_id).delete()
            
            # Analizar celdas con contenido - CORREGIDO PARA MERGED CELLS
            for row in ws.iter_rows():
                for cell in row:
                    # SALTAR CELDAS COMBINADAS
                    if hasattr(cell, '__class__') and cell.__class__.__name__ == 'MergedCell':
                        continue
                    
                    # Solo procesar celdas con contenido
                    if cell.value is not None:
                        try:
                            # Crear celda de plantilla
                            template_cell = TemplateCell(
                                template_id=template_id,
                                cell_address=cell.coordinate,
                                cell_type='static',
                                default_value=str(cell.value),
                                style_config=TemplateService._extract_cell_style(cell)
                            )
                            db.session.add(template_cell)
                        except Exception as e:
                            print(f"Error procesando celda {cell.coordinate}: {e}")
                            continue
            
            # Analizar estilos de columnas
            for col_letter, col_dimension in ws.column_dimensions.items():
                if col_dimension.width:
                    try:
                        template_style = TemplateStyle(
                            template_id=template_id,
                            range_address=f"{col_letter}:{col_letter}",
                            column_width=col_dimension.width
                        )
                        db.session.add(template_style)
                    except Exception as e:
                        print(f"Error procesando columna {col_letter}: {e}")
                        continue
            
            # Analizar estilos de filas
            for row_num, row_dimension in ws.row_dimensions.items():
                if row_dimension.height:
                    try:
                        template_style = TemplateStyle(
                            template_id=template_id,
                            range_address=f"{row_num}:{row_num}",
                            row_height=row_dimension.height
                        )
                        db.session.add(template_style)
                    except Exception as e:
                        print(f"Error procesando fila {row_num}: {e}")
                        continue
            
            db.session.commit()
            print(f"Plantilla {template_id} analizada exitosamente")
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al analizar plantilla: {str(e)}")

    @staticmethod
    def _extract_cell_style(cell):
        """Extrae los estilos de una celda"""
        style_config = {}
        
        try:
            # Fuente
            if cell.font:
                font_color = '000000'  # Default negro
                if cell.font.color and hasattr(cell.font.color, 'rgb') and cell.font.color.rgb:
                    color_value = str(cell.font.color.rgb)
                    # Convertir ARGB a RGB
                    if len(color_value) == 8:
                        font_color = color_value[2:]  # Quitar los primeros 2 caracteres (alpha)
                    elif len(color_value) == 6:
                        font_color = color_value
                
                style_config['font'] = {
                    'name': cell.font.name or 'Arial',
                    'size': cell.font.size or 11,
                    'bold': cell.font.bold or False,
                    'italic': cell.font.italic or False,
                    'color': font_color
                }
            
            # Relleno - SOLO si no es blanco
            if cell.fill and cell.fill.start_color and hasattr(cell.fill.start_color, 'rgb') and cell.fill.start_color.rgb:
                fill_color_value = str(cell.fill.start_color.rgb)
                fill_color = 'FFFFFF'  # Default blanco
                
                if len(fill_color_value) == 8:
                    fill_color = fill_color_value[2:]  # Quitar alpha
                elif len(fill_color_value) == 6:
                    fill_color = fill_color_value
                
                # Solo guardar si NO es blanco
                if fill_color.upper() not in ['FFFFFF', 'FFFFFFFF']:
                    style_config['fill'] = {
                        'color': fill_color
                    }
            
            # Alineación
            if cell.alignment:
                style_config['alignment'] = {
                    'horizontal': cell.alignment.horizontal or 'left',
                    'vertical': cell.alignment.vertical or 'top',
                    'wrap_text': cell.alignment.wrap_text or False
                }
            
            # BORDES - Simplificado
            if cell.border:
                border_config = {}
                
                # Solo capturar si hay bordes visibles
                if cell.border.left and cell.border.left.style:
                    border_config['left'] = cell.border.left.style
                if cell.border.right and cell.border.right.style:
                    border_config['right'] = cell.border.right.style
                if cell.border.top and cell.border.top.style:
                    border_config['top'] = cell.border.top.style
                if cell.border.bottom and cell.border.bottom.style:
                    border_config['bottom'] = cell.border.bottom.style
                
                if border_config:
                    style_config['border'] = border_config
            
            return json.dumps(style_config) if style_config else None
            
        except Exception as e:
            print(f"Error extrayendo estilo de celda {cell.coordinate}: {e}")
            return None

    @staticmethod
    def _extract_cell_style(cell):
        """Extrae los estilos de una celda"""
        style_config = {}
        
        try:
            # Fuente
            if cell.font:
                style_config['font'] = {
                    'name': cell.font.name or 'Arial',
                    'size': cell.font.size or 11,
                    'bold': cell.font.bold or False,
                    'italic': cell.font.italic or False,
                    'color': str(cell.font.color.rgb)[2:] if cell.font.color and cell.font.color.rgb else '000000'
                }
            
            # Relleno
            if cell.fill and cell.fill.start_color and cell.fill.start_color.rgb:
                fill_color = str(cell.fill.start_color.rgb)
                if fill_color != 'FFFFFFFF' and fill_color != 'FFFFFF':
                    style_config['fill'] = {
                        'color': fill_color[2:] if len(fill_color) == 8 else fill_color
                    }
            
            # BORDES - CAPTURAR EL ESTILO ORIGINAL EXACTO
            if cell.border:
                border_config = {}
                
                # Capturar cada lado del borde con su estilo original
                if cell.border.left and cell.border.left.style:
                    border_config['left'] = {
                        'style': cell.border.left.style,
                        'color': str(cell.border.left.color.rgb)[2:] if cell.border.left.color and cell.border.left.color.rgb else '000000'
                    }
                
                if cell.border.right and cell.border.right.style:
                    border_config['right'] = {
                        'style': cell.border.right.style,
                        'color': str(cell.border.right.color.rgb)[2:] if cell.border.right.color and cell.border.right.color.rgb else '000000'
                    }
                
                if cell.border.top and cell.border.top.style:
                    border_config['top'] = {
                        'style': cell.border.top.style,
                        'color': str(cell.border.top.color.rgb)[2:] if cell.border.top.color and cell.border.top.color.rgb else '000000'
                    }
                
                if cell.border.bottom and cell.border.bottom.style:
                    border_config['bottom'] = {
                        'style': cell.border.bottom.style,
                        'color': str(cell.border.bottom.color.rgb)[2:] if cell.border.bottom.color and cell.border.bottom.color.rgb else '000000'
                    }
                
                if border_config:
                    style_config['border'] = border_config
            
            # Alineación
            if cell.alignment:
                style_config['alignment'] = {
                    'horizontal': cell.alignment.horizontal or 'left',
                    'vertical': cell.alignment.vertical or 'top',
                    'wrap_text': cell.alignment.wrap_text or False
                }
            
            return json.dumps(style_config) if style_config else None
            
        except Exception as e:
            print(f"Error extrayendo estilo: {e}")
            return None

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
