from flask_login import UserMixin

class Student(UserMixin):
    def __init__(self, id, student_number, password, last_name, first_name):
        self.id = id
        self.student_number = student_number
        self.password = password
        self.last_name = last_name
        self.first_name = first_name
        self.role = 'student'
