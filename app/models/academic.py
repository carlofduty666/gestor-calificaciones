from app import db
from datetime import datetime

class AcademicYear(db.Model):
    __tablename__ = 'academic_years'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    periods = db.relationship('Period', backref='academic_year', lazy='dynamic', cascade='all, delete-orphan')
    teacher_assignments = db.relationship('TeacherAssignment', backref='academic_year', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<AcademicYear {self.name}>'

class Period(db.Model):
    __tablename__ = 'periods'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    grade_types = db.relationship('GradeType', backref='period', lazy='dynamic', cascade='all, delete-orphan')
    student_grades = db.relationship('StudentGrade', backref='period', lazy='dynamic', cascade='all, delete-orphan')
    final_grades = db.relationship('FinalGrade', backref='period', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Period {self.name}>'

class Grade(db.Model):
    __tablename__ = 'grades'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    level = db.Column(db.String(64), nullable=False)  # Primaria, Secundaria, etc.
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    sections = db.relationship('Section', backref='grade', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Grade {self.name}>'

class Section(db.Model):
    __tablename__ = 'sections'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False)  # A, B, C, etc.
    grade_id = db.Column(db.Integer, db.ForeignKey('grades.id'), nullable=False)
    capacity = db.Column(db.Integer, default=30)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    students = db.relationship('Student', backref='section', lazy='dynamic', cascade='all, delete-orphan')
    teacher_assignments = db.relationship('TeacherAssignment', backref='section', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Section {self.grade.name}{self.name}>'
    
subject_grade = db.Table('subject_grade',
    db.Column('subject_id', db.Integer, db.ForeignKey('subjects.id'), primary_key=True),
    db.Column('grade_id', db.Integer, db.ForeignKey('grades.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class Subject(db.Model):
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    teacher_assignments = db.relationship('TeacherAssignment', backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    grade_types = db.relationship('GradeType', backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    student_grades = db.relationship('StudentGrade', backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    final_grades = db.relationship('FinalGrade', backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    grades = db.relationship('Grade', secondary=subject_grade, backref=db.backref('subjects', lazy='dynamic'))

    def __repr__(self):
        return f'<Subject {self.name}>'

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    student_id = db.Column(db.String(20), nullable=False, unique=True)
    birth_date = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(1), nullable=True)  # M, F
    address = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    student_grades = db.relationship('StudentGrade', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    final_grades = db.relationship('FinalGrade', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.last_name}, {self.first_name}>'
    
    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    first_name = db.Column(db.String(64), nullable=True)  # Para casos donde se crea automáticamente
    last_name = db.Column(db.String(64), nullable=True)   # Para casos donde se crea automáticamente
    employee_id = db.Column(db.String(20), unique=True, nullable=True)  # Para identificación
    specialization = db.Column(db.String(100))
    qualification = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    identification_number = db.Column(db.String(20), unique=True)
    is_registered = db.Column(db.Boolean, default=False)
    hire_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con asignaciones
    assignments = db.relationship('TeacherAssignment', backref='teacher', lazy='dynamic')
    
    def __repr__(self):
        if self.first_name and self.last_name:
            return f'<Teacher {self.first_name} {self.last_name}>'
        return f'<Teacher {self.user.first_name} {self.user.last_name}>'
    
    # Método helper para obtener el nombre completo
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        return f'{self.user.first_name} {self.user.last_name}'


class TeacherAssignment(db.Model):
    __tablename__ = 'teacher_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Asegurarse de que las relaciones estén correctamente definidas
    # teacher = db.relationship('Teacher', backref='assignments')
    # subject = db.relationship('Subject', backref='assignments')
    # section = db.relationship('Section', backref='assignments')
    # academic_year = db.relationship('AcademicYear', backref='assignments')
    
    def __repr__(self):
        return f'<TeacherAssignment {self.teacher.user.last_name} - {self.subject.name} - {self.section.grade.name}{self.section.name}>'
    
    # Método para verificar si la asignación está activa
    def is_active(self):
        return self.academic_year.is_active

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<Admin {self.user.first_name} {self.user.last_name}>'
