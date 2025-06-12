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
