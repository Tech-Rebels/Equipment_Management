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
            data = {}
            try:
                student = Student.objects.get(rfidno=rfid)
                pending_equipment = Manage_Equiment.objects.filter(regno=student.regno, status=False)
                if pending_equipment.exists():
                    data['error'] = 'You have pending equipment to return'
                else:
                    data = {
                        'name': student.name,
                        'regno': student.regno,
                    }
            except Student.DoesNotExist:
                data['error'] = 'Student not found'
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
                            category=category,borrowed_date=date)
    messages.success(request,'Equipment saved successsfully')
    return redirect('index')


def return_equipments(request):
    if request.method == 'GET':
        rfid = request.GET.get('rfid')
        if rfid:
            data = {}
            try:
                student = Student.objects.get(rfidno=rfid)
                manage_equipment = Manage_Equiment.objects.filter(regno=student.regno, status=False)
                equipment_names = [equipment.category for equipment in manage_equipment]
                if not manage_equipment.exists():
                    data['error'] = 'You do not have pending equipment to return'
                else:
                    data = {
                        'name': student.name,
                        'regno': student.regno,
                        'equipments': ', '.join(equipment_names),
                    }
            except Student.DoesNotExist:
                data = {'error': 'Student not found'}
            return JsonResponse(data)
        
        return render(request,'equiments/return_equiments.html')

    if request.method == 'POST':
        
        return_date = request.POST['date']
        return_time = request.POST['time']
        stud_reg = request.POST['regno']
        
        try:
            manage_equipment = Manage_Equiment.objects.filter(regno=stud_reg,status=False)
        
        # Iterate over each Manage_Equiment object and update its attributes
            for equipment in manage_equipment:
                equipment.returned_date = return_date
                equipment.returned_time = return_time
                equipment.status = True
                equipment.save()
            messages.success(request, 'Equipment returned successfully')
        except Manage_Equiment.DoesNotExist:
            messages.error(request, 'Equipment with this regno does not exist')
        
        return redirect('index')