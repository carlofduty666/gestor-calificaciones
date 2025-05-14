from app import db
from datetime import datetime

class GradeType(db.Model):
    __tablename__ = 'grade_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    weight = db.Column(db.Float, nullable=False, default=1.0)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    period_id = db.Column(db.Integer, db.ForeignKey('periods.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    student_grades = db.relationship('StudentGrade', backref='grade_type', lazy='dynamic', cascade='all, delete-orphan')
    teacher = db.relationship('Teacher', backref='grade_types')
    section = db.relationship('Section', backref='grade_types')
    
    def __repr__(self):
        return f'<GradeType {self.name}>'

class StudentGrade(db.Model):
    __tablename__ = 'student_grades'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    grade_type_id = db.Column(db.Integer, db.ForeignKey('grade_types.id'), nullable=False)
    period_id = db.Column(db.Integer, db.ForeignKey('periods.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<StudentGrade {self.student.last_name} - {self.subject.name} - {self.grade_type.name} - {self.value}>'

class FinalGrade(db.Model):
    __tablename__ = 'final_grades'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    period_id = db.Column(db.Integer, db.ForeignKey('periods.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<FinalGrade {self.student.last_name} - {self.subject.name} - {self.value}>'
