from app import db
from datetime import datetime
import json

class ExcelTemplate(db.Model):
    __tablename__ = 'excel_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    template_type = db.Column(db.String(50), nullable=False)  # 'section_report', 'student_report', etc.
    file_path = db.Column(db.String(255))
    design_config = db.Column(db.Text)  # JSON con la configuración del diseño
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    
    # Relaciones
    creator = db.relationship('User', backref='excel_templates')
    cells = db.relationship('TemplateCell', backref='template', cascade='all, delete-orphan')
    styles = db.relationship('TemplateStyle', backref='template', cascade='all, delete-orphan')
    ranges = db.relationship('TemplateRange', backref='template', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ExcelTemplate {self.name}>'
    
    def get_design_config(self):
        if self.design_config:
            return json.loads(self.design_config)
        return {}
    
    def set_design_config(self, config):
        self.design_config = json.dumps(config)

class TemplateCell(db.Model):
    __tablename__ = 'template_cells'
    
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('excel_templates.id'), nullable=False)
    cell_address = db.Column(db.String(10), nullable=False)  # A1, B2, etc.
    cell_type = db.Column(db.String(20), default='static')   # static o data
    data_type = db.Column(db.String(50))                     # cedula, nombre, apellido, nota, etc.
    content_type = db.Column(db.String(50))                  # ← AGREGAR ESTA LÍNEA
    default_value = db.Column(db.Text)
    style_config = db.Column(db.Text)                        # JSON con estilos
    extra_config = db.Column(db.Text)
    
    # Relación
    # template = db.relationship('ExcelTemplate', backref='cells')
    
    def __repr__(self):
        return f'<TemplateCell {self.cell_address}: {self.data_type}>'


class TemplateStyle(db.Model):
    __tablename__ = 'template_styles'
    
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('excel_templates.id'), nullable=False)
    range_address = db.Column(db.String(20), nullable=False)  # A1:C3, A:A, 1:1, etc.
    column_width = db.Column(db.Float)
    row_height = db.Column(db.Float)
    merge_cells = db.Column(db.Boolean, default=False)
    style_config = db.Column(db.Text)  # JSON con configuración de estilos
    
    def __repr__(self):
        return f'<TemplateStyle {self.range_address}>'
    
class TemplateRange(db.Model):
    """Configuración de rangos de celdas para datos iterativos"""
    __tablename__ = 'template_ranges'
    
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('excel_templates.id'), nullable=False)
    range_name = db.Column(db.String(50), nullable=False)  # ej: "lista_estudiantes"
    start_cell = db.Column(db.String(10), nullable=False)  # ej: "A12"
    end_cell = db.Column(db.String(10))                    # ej: "F50" (opcional)
    range_type = db.Column(db.String(20), nullable=False)  # "students", "subjects", "static"
    data_mapping = db.Column(db.Text)                      # JSON con mapeo de columnas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TemplateRange {self.range_name}: {self.start_cell}>'

