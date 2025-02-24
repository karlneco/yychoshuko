from sqlalchemy import func

from yychoshuko import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def load_grade(grade_id):
    return Grade.query.get(grade_id)


staff_grade = db.Table(
    "staff_grade",
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('grade_id', db.Integer, db.ForeignKey('grade.id')),
)

class Grade(db.Model):
    __tablename__ = 'grade'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    instructions = db.Column(db.String(512), nullable=True)
    day_start = db.Column(db.Time, nullable=True)
    lunch_start = db.Column(db.Time, nullable=True)
    lunch_end = db.Column(db.Time, nullable=True)
    day_end = db.Column(db.Time, nullable=True)
    staff = db.relationship('User', secondary=staff_grade, back_populates='grades')
    absences = db.relationship('Absence', back_populates='grade')

    def __repr__(self):
        teacher_names = ', '.join(teacher.name for teacher in self.staff) if self.staff else 'No Teachers'
        return f"<Grade {self.name}, Teachers: {teacher_names}>"


class SchoolClass(db.Model):
    __tablename__ = 'class'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)  # The class name
    year = db.Column(db.Integer, nullable=False)  # The current academic year for the class
    start_year = db.Column(db.Integer, nullable=False)  # The year this collection of students started in grade 1
    grade_id = db.Column(db.Integer, db.ForeignKey('grade.id'), nullable=False)

    # Establish relationship with Grade
    grade = db.relationship('Grade', backref=db.backref('classes', lazy=True))

    def __repr__(self):
        return (f"<SchoolClass {self.name}, Grade: {self.grade.name}, Current Year: {self.year}, "
                f"Started: {self.start_year}>")

class Absence(db.Model):
    __tablename__ = 'absence'
    id = db.Column(db.Integer, primary_key=True)
    parent_email = db.Column(db.String(128))
    student_name = db.Column(db.String(64), index=True)
    reason = db.Column(db.String(256))
    absence_type = db.Column(db.String(256))
    date = db.Column(db.Date)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    comment = db.Column(db.String(512), nullable=True)
    class_id = db.Column(db.Integer, db.ForeignKey('grade.id'))
    grade = db.relationship('Grade', back_populates='absences')
    created_at = db.Column(db.DateTime, default=func.now())  # New field for creation timestamp

    def __repr__(self):
        return f'<Absence {self.student_name} {self.date}>'


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(64))
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)
    user_type = db.Column(db.String(1), default="N")
    grades = db.relationship('Grade', secondary=staff_grade, back_populates='staff')

    def __init__(self, email, password, name, user_type):
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.name = name
        self.user_type = user_type

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return self.email


class Semester(db.Model):
    __tablename__ = 'semester'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<Semester {self.name} from {self.start_date} to {self.end_date}>'


class Student(db.Model):
    __tablename__ = 'student'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)  # Optional
    date_of_birth = db.Column(db.Date, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    parents_email = db.Column(db.String(120), nullable=False)

    # Foreign key linking to the SchoolClass table (whose __tablename__ is 'class')
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=True)

    # Relationship to the SchoolClass model
    school_class = db.relationship('SchoolClass', backref=db.backref('students', lazy=True))

    def __repr__(self):
        # If a student is assigned a class and that class has an associated grade,
        # display the grade name. Otherwise, show "No Grade".
        grade_name = self.school_class.grade.name if (self.school_class and self.school_class.grade) else "No Grade"
        return f'<Student {self.first_name} {self.last_name}, Grade: {grade_name}>'
