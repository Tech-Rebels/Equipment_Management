from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Student(models.Model):
    rfidno = models.CharField(max_length=100, unique=True)
    regno = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    image = models.ImageField(default='avatar.png', upload_to='Student_Images')
    dob = models.DateField(null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=10, null=True, blank=True)
    # department = models.CharField(max_length=100, null=True)
    # course = models.CharField(max_length=100, null=True)
    year = models.IntegerField(null=True)

    def __str__(self):
        return f"{self.regno} - {self.name} - {self.rfidno}"
    
class Equipment(models.Model):
    lab = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100, null=True)
    order = models.IntegerField(null=True, blank=True)
    count = models.IntegerField()
    available_count = models.IntegerField(null=True, blank=True)
    category = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.lab.username} - {self.name}"

class Transaction(models.Model):
    student = models.ForeignKey(Student, null=True, on_delete=models.SET_NULL)
    equipment = models.ManyToManyField(Equipment)
    borrowed_at = models.DateTimeField()
    returned_at = models.DateTimeField(null=True, blank=True)
    status = models.BooleanField(default=False)
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        equipment_names = ', '.join([equipment.name for equipment in self.equipment.all()]) if self.equipment.exists() else 'Unknown'
        return_status = 'Returned' if self.status == True else 'Not Returned'
        return f"{self.borrowed_at if self.borrowed_at else 'Unknown'} - {self.handled_by.username if self.handled_by else 'Unknown'} - {self.student.regno if self.student else 'Unknown'} - {equipment_names} - {return_status}"
