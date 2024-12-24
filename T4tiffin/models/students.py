from django.db import models


class StudentRegistration(models.Model):
    username = models.CharField(max_length=100, unique= True)
    password = models.CharField(max_length=255)
    student_name = models.CharField(max_length=100)
    parent_name = models.CharField(max_length=100)
    standard = models.CharField(max_length=10)
    division = models.CharField(max_length=10)
    parent_phone = models.CharField(max_length=15)
    roll_no = models.CharField(max_length=100, default="")
    actual_password = models.CharField(max_length=100, default="")
    address = models.TextField()





    def register(self):

        self.save()

    @staticmethod
    def get_student_by_user(username):
        try:
            return StudentRegistration.objects.get(username = username)
        except:
            return False




    def isExist(self):
        if StudentRegistration.objects.filter(username = self.username):
            return True
        return False