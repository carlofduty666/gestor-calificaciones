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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    students = db.relationship('Student', backref='section', lazy='dynamic', cascade='all, delete-orphan')
    teacher_assignments = db.relationship('TeacherAssignment', backref='section', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Section {self.grade.name}{self.name}>'

class Subject(db.Model):
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    teacher_assignments = db.relationship('TeacherAssignment', backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    grade_types = db.relationship('GradeType', backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    student_grades = db.relationship('StudentGrade', backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    final_grades = db.relationship('FinalGrade', backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    
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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    specialization = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    assignments = db.relationship('TeacherAssignment', backref='teacher', lazy='dynamic', cascade='all, delete-orphan')
    student_grades = db.relationship('StudentGrade', backref='teacher', lazy='dynamic')
    
    def __repr__(self):
        return f'<Teacher {self.user.last_name}, {self.user.first_name}>'
    
    def get_full_name(self):
        return self.user.get_full_name()

class TeacherAssignment(db.Model):
    __tablename__ = 'teacher_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TeacherAssignment {self.teacher.user.last_name} - {self.subject.name} - {self.section.grade.name}{self.section.name}>'


class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    department = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Admin {self.user.last_name}, {self.user.first_name}>'
    
    def get_full_name(self):
        return self.user.get_full_name()
