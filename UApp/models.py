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
    year = models.CharField(max_length=100, null=True, blank=True)

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

class MedicalKit(models.Model):
    lab = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    kitName = models.CharField(max_length=100, null=False, blank=False)
    equipment = models.ManyToManyField(Equipment)
    order = models.IntegerField(null=True, blank=True)

    def __str__(self):
        equipment_names = ', '.join(equipment.name for equipment in self.equipment.all())
        return f"{self.kitName} - {self.lab.username} - {equipment_names}"
    
class Treatment(models.Model):
    lab = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    treatment = models.CharField(max_length=100, null=False, blank=False)
    order = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.treatment} - {self.lab.username}"

class Transaction(models.Model):
    student = models.ForeignKey(Student, null=True, on_delete=models.SET_NULL)
    studentName = models.CharField(max_length=100, null=True)
    studentRegno = models.CharField(max_length=100, null=True)
    equipment = models.ManyToManyField(Equipment)
    equipmentName = models.CharField(max_length=200, null=True)
    treatment = models.ManyToManyField(Treatment)
    treatmentName = models.CharField(max_length=200, null=True)
    borrowed_at = models.DateTimeField()
    returned_at = models.DateTimeField(null=True, blank=True)
    status = models.BooleanField(default=False)
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    labName = models.CharField(max_length=100, null=True)

    def save(self, *args, **kwargs):
        if self.student:
            self.studentName = self.student.name
            self.studentRegno = self.student.regno
        else:
            self.studentName = 'Unknown'
            self.studentRegno = 'Unknown'
        if self.handled_by:
            self.labName = self.handled_by.username
        else:
            self.labName = 'Unknown'

        super().save(*args, **kwargs)

        equipment_names = ', '.join(equipment.name for equipment in self.equipment.all())
        self.equipmentName = equipment_names if equipment_names else 'Unknown'

        treatment_names = ', '.join(treatment.treatment for treatment in self.treatment.all())
        self.treatmentName = treatment_names if treatment_names else 'Unknown'

        super().save(update_fields=['studentName', 'studentRegno', 'equipmentName', 'treatmentName'])

    def __str__(self):
        return_status = 'Returned' if self.status == True else 'Not Returned'
        return f"{self.borrowed_at if self.borrowed_at else 'Unknown'} - {self.labName} - {self.studentRegno} - {self.equipmentName} - {self.treatmentName} - {return_status}"
