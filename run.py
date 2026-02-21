from app import create_app, db
from app.models.users import User
from app.models.academic import AcademicYear, Period, Grade, Section, Subject, Student, Teacher, TeacherAssignment, Admin
from app.models.grades import GradeType, StudentGrade, FinalGrade

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Teacher': Teacher, 
        'Admin': Admin,
        'AcademicYear': AcademicYear,
        'Period': Period,
        'Grade': Grade,
        'Section': Section,
        'Subject': Subject,
        'Student': Student,
        'TeacherAssignment': TeacherAssignment,
        'GradeType': GradeType,
        'StudentGrade': StudentGrade,
        'FinalGrade': FinalGrade
    }

if __name__ == '__main__':
    app.run(debug=True)