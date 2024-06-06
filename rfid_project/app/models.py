from django.db import models
from django.utils.timezone import now

# Create your models here.
class Student(models.Model):
    rfidno = models.CharField(max_length=100, unique=True)
    regno = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=10, null=True, blank=True)
    department = models.CharField(max_length=100, null=True)
    course = models.CharField(max_length=100, null=True)
    year = models.IntegerField()
    def __str__(self):
        return self.name 
    
class Manage_Equiment(models.Model):
    borrowed_date = models.DateField(default=now)
    borrowed_time = models.TimeField()
    regno = models.CharField(max_length=100)
    stud_name = models.CharField(max_length=100,null=True)
    category = models.CharField(max_length=266)
    returned_time = models.TimeField(null=True, blank=True)
    returned_date = models.DateField(null=True, blank=True)
    status = models.BooleanField(default=False)
     # stud_name = models.ForeignKey(Student, null=True, on_delete=models.SET_NULL)
    # handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    # Lab = models.CharField(max_length=100, default='Default Lab')


    def __str__(self):
        return self.regno    
    class Meta:
        ordering: ['-date'] # type: ignore

    # def _str_(self):
    #     return f"{self.borrowed_at if self.borrowed_at else 'Unknown'} - {self.handled_by.username if self.handled_by else 'Unknown'} - {self.student.regno if self.student else 'Unknown'} - {self.equipment.name if self.equipment else 'Unknown'}"
    # class Meta:
    #     ordering = ['-borrowed_at']

class Equiment(models.Model):
    name = models.CharField(max_length=100, null=True)
    idno = models.CharField(max_length=100, null=True, blank=True)
    count = models.IntegerField(default=0)
    available = models.BooleanField(default=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    # lab = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return self.idno
    # def _str_(self):
    #     return f"{self.lab.username} - {self.name}"
    

      
class Category(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'Categories'    

    def __str__(self) :
        return self.name