from flask_login import UserMixin

class Student(UserMixin):
    def __init__(self, id, student_number, password, last_name, first_name, gender, in_lecture, right_eye_baseline, left_eye_baseline):
        self.id = id
        self.student_number = student_number
        self.password = password
        self.last_name = last_name
        self.first_name = first_name
        self.gender = gender
        self.in_lecture = in_lecture
        self.right_eye_baseline = right_eye_baseline
        self.left_eye_baseline = left_eye_baseline
        self.role = 'student'

