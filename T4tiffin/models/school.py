from django.db import models

class School(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    school_name = models.CharField(max_length=100)
    

    @staticmethod
    def get_school_by_user(username):
        try:
            return School.objects.get(username = username)
        except:
            return False