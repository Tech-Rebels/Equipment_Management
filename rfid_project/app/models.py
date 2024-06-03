from django.db import models
from django.utils.timezone import now

# Create your models here.
class Manage_Equiment(models.Model):
    date = models.DateField(default=now)
    borrowed_time = models.TimeField()
    regno = models.CharField(max_length=100)
    stud_name = models.CharField(max_length=100)
    category = models.CharField(max_length=266)
    # rfidno = models.CharField(max_length=100, unique=True)
    # Lab = models.CharField(max_length=100, default='Default Lab')
    # email = models.EmailField(default='default@example.com')

    def __str__(self):
        return self.regno    
    class Meta:
        ordering: ['-date'] # type: ignore
class Equiment(models.Model):
    eq_name = models.CharField(max_length=100)
    Lab = models.CharField(max_length=100, default='01')
    eq_id = models.CharField(max_length=100)
    def __str__(self):
        return self.eq_id
    
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
      
class Category(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'Categories'    

    def __str__(self) :
        return self.name