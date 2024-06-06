from django.shortcuts import render,redirect
from .models import Category,Manage_Equiment,Student
from django.contrib import messages
from django.http import JsonResponse

# Create your views here.
def index(request):
    categories = Category.objects.all()
    equiment = Manage_Equiment.objects.all() 
    context = {
        'equiment' : equiment
    } 
    return render(request,'equiments/index.html',context)

def add_equiments(request):
    categories = Category.objects.all()
    context = {
        'categories': categories,
        'values':request.POST
    }
    if request.method == 'GET':
        rfid = request.GET.get('rfid')
        if rfid:
            try:
                student = Student.objects.get(rfidno=rfid)
                data = {
                    'name': student.name,
                    'regno': student.regno,
                    # 'email': student.email,
                }
            except Student.DoesNotExist:
                data = {'error': 'Student not found'}
            return JsonResponse(data)
        
        return render(request,'equiments/add_equiments.html',context)
    if request.method == 'POST':
        regno = request.POST['regno']
        if not regno:
            messages.error(request,'regno is required')
            return render(request,'equiments/add_equiments.html', context)

        stud_name = request.POST['stud_name']
        date = request.POST['date']
        category = request.POST['category']
        time = request.POST['time']
        
        # email = request.POST['email']
        if not stud_name:
            messages.error(request,'stud_name is required')
            return render(request,'equiments/add_equiments.html', context)
         
    Manage_Equiment.objects.create(regno=regno,stud_name=stud_name,borrowed_time=time,
                            category=category,date=date)
    messages.success(request,'Equiment saved successsfully')
    return redirect('index')


def return_equipments(request):

    return render(request,'equiments/return_equiments.html')

