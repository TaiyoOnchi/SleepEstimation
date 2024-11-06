from flask_login import UserMixin

class Teacher(UserMixin):
    def __init__(self, id, teacher_number, password, last_name, first_name):
        self.id = id
        self.teacher_number = teacher_number
        self.password = password
        self.last_name = last_name
        self.first_name = first_name
        self.role = 'teacher'
    
    def get_id(self):
        return str(self.id)
