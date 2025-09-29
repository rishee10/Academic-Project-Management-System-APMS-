from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    full_name = models.CharField(max_length=100)
    section = models.CharField(max_length=10)
    passing_year = models.IntegerField()
    branch = models.CharField(max_length=50)
    degree = models.CharField(max_length=50)
    mobile_no = models.CharField(max_length=15)
    email_id = models.EmailField()
    abc_id = models.CharField(max_length=20, unique=True)
    id_card_photo = models.ImageField(upload_to='id_cards/')
    
    def __str__(self):
        return self.full_name

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    full_name = models.CharField(max_length=100)
    mobile_no = models.CharField(max_length=15)
    email_id = models.EmailField()
    department = models.CharField(max_length=50)
    
    def __str__(self):
        return self.full_name