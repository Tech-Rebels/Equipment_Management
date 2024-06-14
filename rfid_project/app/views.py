from django.shortcuts import render,redirect
from .models import Category,Manage_Equiment,Student,Equiment
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from app.forms import CreateUserForm
from django.contrib.auth import  authenticate,login,logout
from django.core.paginator import Paginator
# Create your views here.
def index(request):
    categories = Category.objects.all()
    # equiment = Manage_Equiment.objects.all() 
    equipment = Manage_Equiment.objects.filter(handled_by=request.user)
    paginator = Paginator(equipment,10)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator,page_number)
    context = {
        'equiment' : equipment,
        'page_obj' : page_obj
    } 
    return render(request,'equiments/index.html',context)

def borrow_equiments(request):
    if not request.user.is_authenticated:
        return redirect('login')  # Redirect to login page if user is not authenticated
    
    equipment_names = Equiment.objects.filter(lab=request.user).values_list('name', flat=True).distinct()
    categories = Category.objects.all()
    context = {
        'equipment_names': equipment_names,
        'categories': categories,
        'values': request.POST
    }

    if request.method == 'GET':
        rfid = request.GET.get('rfid')
        if rfid:
            data = {}
            try:
                student = Student.objects.get(rfidno=rfid)
                pending_equipment = Manage_Equiment.objects.filter(regno=student.regno, status=False, handled_by=request.user)
                if pending_equipment.exists():
                    data['error'] = 'You have pending equipment to return'
                else:
                    data = {
                        'name': student.name,
                        'regno': student.regno,
                        'image_url': student.photo.url if student.photo else '',
                    }
            except Student.DoesNotExist:
                data['error'] = 'Student not found'
            return JsonResponse(data)
        
        return render(request, 'equiments/borrow_equiments.html', context)
    
    if request.method == 'POST':
        regno = request.POST['regno']
        stud_name = request.POST['stud_name']
        date = request.POST['date']
        category = request.POST['equipment']
        time = request.POST['time']

        try:
            equipment = Equiment.objects.get(name=category, lab=request.user)
            equipment.available = False  # Mark the equipment as not available
            equipment.save()  # Save the updated equipment
        except Equiment.DoesNotExist:
            messages.error(request, 'Equipment not found')
            return render(request, 'equiments/borrow_equiments.html', context)

        if not stud_name:
            messages.error(request, 'Student name is required')
            return render(request, 'equiments/borrow_equiments.html', context)
        
        Manage_Equiment.objects.create(
            regno=regno,
            stud_name=stud_name,
            borrowed_time=time,
            category=category,
            borrowed_date=date,
            handled_by=request.user
        )

        messages.success(request, 'Equipment borrowed successfully')
        return redirect('index')


def return_equipments(request):
    if request.method == 'GET':
        rfid = request.GET.get('rfid')
        if rfid:
            data = {}
            try:
                student = Student.objects.get(rfidno=rfid)
                manage_equipment = Manage_Equiment.objects.filter(regno=student.regno, status=False,handled_by=request.user)
                equipment_names = [equipment.category for equipment in manage_equipment]
                if not manage_equipment.exists():
                    data['error'] = 'You do not have pending equipment to return'
                else:
                    data = {
                        'name': student.name,
                        'regno': student.regno,
                        'image_url': student.photo.url if student.photo else '',
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
        equipment = request.POST['taken_eq']
        
        try:
            manage_equipment = Manage_Equiment.objects.filter(regno=stud_reg,status=False,handled_by=request.user)
            equipment = Equiment.objects.get(name=equipment, lab=request.user)
        # Iterate over each Manage_Equiment object and update its attributes
            for equipment in manage_equipment:
                equipment.returned_date = return_date
                equipment.returned_time = return_time
                equipment.status = True
                equipment.save()
            
                # Update the 'available' attribute to True
            equipment.available = True
            equipment.save()  
            messages.success(request, 'Equipment returned successfully')
        except Manage_Equiment.DoesNotExist:
            messages.error(request, 'Equipment with this regno does not exist')
       

        
        return redirect('index')
 

def register_page(request):
    form=CreateUserForm()
    if request.method=='POST':
        form=CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Registration Success You can Login Now ..!")
            return redirect('login')
    return render(request,'authentication/register.html',{'form':form})

def logout_page(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request,"Logged out Successfully")
    return redirect("login")

   
def login_page(request):
    if request.user.is_authenticated:
        return redirect("index")
    else:
        if request.method == 'POST':
            name=request.POST.get('username')
            pwd=request.POST.get('password')
            user = authenticate(request,username=name,password=pwd)
            if user is not None:
                login(request,user)
                messages.success(request,"Logged in successfully")
                return redirect("index")
            else:
                messages.error(request,"Invalid User Name or Password")
                return redirect("/login")

    return render(request,'authentication/login.html')


        

def history(request):
    equipment = Manage_Equiment.objects.filter(handled_by=request.user)
    paginator = Paginator(equipment,10)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator,page_number)
    context = {
        'equiment' : equipment,
        'page_obj' : page_obj
    } 
    return render(request,'equiments/history.html',context)
# Equipments
def equipments(request):
    equipment = Equiment.objects.filter(lab=request.user) 
    context = {
        'equipment': equipment
    }
    return render(request,'equiments/equipments.html',context)

def add_equiments(request):
    if request.method == 'GET':
        return render(request,'equiments/add_equiments.html' )
    
    if request.method == 'POST':
        name = request.POST['name']
        count = request.POST['count']
        if not name:
            messages.error(request,'name is required')
            return render(request,'equiments/add_equiments.html')
         
    Equiment.objects.create(name=name,count=count,
                            lab=request.user)
    messages.success(request,'Equipment saved successsfully')
    return redirect('index')

def edit_equipment(request,id):
    try:
        equipment = Equiment.objects.get(lab=request.user, id=id)
    except Equiment.DoesNotExist:
        messages.error(request, 'Equipment not found.')
        return redirect('equipments')

    context = {
        'equipment': equipment,
        'values': equipment,
    }

    if request.method == 'GET':

        return render(request,'equiments/edit_equipments.html',context)
    # else:
    #     messages.info(request,'Handling post form')
    #     return render(request,'equiments/edit_equipments.html',context)
    
    if request.method == 'POST':
        equipment = Equiment.objects.get(id=id, lab=request.user)
        name = request.POST['name']
        count = request.POST['count']
        if not name:
            messages.error(request,'name is required')
            return render(request,'equiments/edit_equipments.html')
         
        equipment.name = name
        equipment.count = count
        equipment.save()
    messages.success(request,'Equipment saved successsfully')
    return redirect('equipments')
def delete_equipment(request,id):
    equipment = Equiment.objects.get(id=id, lab=request.user)
    equipment.delete()
    messages.success(request,'Equipment Deleted Successsfully')
    return redirect('equipments')