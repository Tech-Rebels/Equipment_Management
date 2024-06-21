import json
import pandas as pd
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Count, Sum, Q, F, Max, BooleanField, Case, When, Value, CharField
from django.db.models.functions import Concat
from django.db import transaction as db_transaction
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .forms import CreateUserForm, UserEditForm, AddEquipmentForm, EquipmentForm
from .models import Equipment, Student, Transaction


# 
# check fn - user or admin 
def is_admin(user):
    return user.is_staff

def is_user(user):
    return not user.is_staff and not user.is_superuser

def user_passes_test_custom(test_func, redirect_to):
    def decorator(view_func):
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            return redirect(redirect_to)
        return _wrapped_view
    return decorator


# error handling
def handling_404(request, exception):
    return render(request, 'UApp/404.html', {})

# register  page - not used
def register(request):
    if request.method == 'POST':
        # form = UserCreationForm(request.POST)
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard-index')
            # return redirect('Login')
    else:
        # form = UserCreationForm()
        form = CreateUserForm()
    context = {
        'form': form
    }
    return render(request, 'UApp/Auth/register.html', context)


# 
# index
@login_required
def index(request):
    if not request.user.is_staff:
        # card
        today = timezone.localdate()
        total_equipment_count = Equipment.objects.filter(lab=request.user).aggregate(Sum('count'))
        borrowed_count_data = Transaction.objects.filter(handled_by=request.user, borrowed_at__date=today).annotate(equipment_count=Count('equipment')).aggregate(total=Sum('equipment_count'))
        not_returned_count_data = Transaction.objects.filter(handled_by=request.user, status=False, borrowed_at__date=today).annotate(equipment_count=Count('equipment')).aggregate(total=Sum('equipment_count'))
        borrowed_count = borrowed_count_data['total'] or 0
        not_returned_count = not_returned_count_data['total'] or 0
        returned_count = borrowed_count - not_returned_count

        # table data
        transactions_list = Transaction.objects.filter(handled_by=request.user, borrowed_at__date=today).order_by('borrowed_at') # , borrowed_at__date=today
        no_of_items = 13
        paginator = Paginator(transactions_list, no_of_items)
        page = request.GET.get('page')
        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            items = paginator.page(1)
        except EmptyPage:
            items = paginator.page(paginator.num_pages)

        context = {
            'items': items,
            'total_equipment_count': total_equipment_count['count__sum'] or 0,
            'borrowed_count': borrowed_count,
            'not_returned_count': not_returned_count,
            'returned_count': returned_count
        }
        return render(request, 'UApp/index.html', context)
    elif request.user.is_staff: #and not request.user.is_superuser:
        users = User.objects.filter(is_staff=False, is_superuser=False)
        context = {
            'users' : users
        }
        return render(request, 'UApp/index.html', context)

@user_passes_test_custom(is_admin, 'dashboard-index')
def admin_dashboard(request, pk):
    lab = get_object_or_404(User, pk=pk)
    # card
    today = timezone.localdate()
    total_equipment_count = Equipment.objects.filter(lab=lab).aggregate(Sum('count'))
    borrowed_count_data = Transaction.objects.filter(handled_by=lab, borrowed_at__date=today).annotate(equipment_count=Count('equipment')).aggregate(total=Sum('equipment_count'))
    not_returned_count_data = Transaction.objects.filter(handled_by=lab, status=False, borrowed_at__date=today).annotate(equipment_count=Count('equipment')).aggregate(total=Sum('equipment_count'))
    borrowed_count = borrowed_count_data['total'] or 0
    not_returned_count = not_returned_count_data['total'] or 0
    returned_count = borrowed_count - not_returned_count

    # table data
    transactions_list = Transaction.objects.filter(handled_by=lab, borrowed_at__date=today).order_by('borrowed_at') # , borrowed_at__date=today
    no_of_items = 13
    paginator = Paginator(transactions_list, no_of_items)
    page = request.GET.get('page')
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)

    context = {
        'lab' : lab,
        'items': items,
        'total_equipment_count': total_equipment_count['count__sum'] or 0,
        'borrowed_count': borrowed_count,
        'not_returned_count': not_returned_count,
        'returned_count': returned_count
    }
    return render(request, 'UApp/Admin/dashboard.html', context)


# 
# settings & about
@login_required
def settings(request):
    return render(request, 'UApp/settings.html')

@login_required
def about(request):
    return render(request, 'UApp/about.html')


# 
# history
@user_passes_test_custom(is_user, 'dashboard-index')
def History(request):
    # table data
    transactions_list = Transaction.objects.filter(handled_by=request.user).order_by('-borrowed_at')
    no_of_items = 15
    paginator = Paginator(transactions_list, no_of_items)
    page = request.GET.get('page')
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)

    context = {
        'items': items,
    }
    return render(request, 'UApp/history.html', context)

@login_required
def history_filter(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        search_str = data.get('searchText', '')
        from_date_str = data.get('fromDate', '')
        to_date_str = data.get('toDate', '')
        return_status = data.get('returnStatus', 'all')

        transactions = Transaction.objects.filter(handled_by=request.user)

        if search_str:
            transactions = transactions.filter(
                Q(student__name__icontains=search_str) |
                Q(student__regno__icontains=search_str) |
                Q(equipment__name__icontains=search_str)
            ).distinct()

        if from_date_str:
            from_date = parse_date(from_date_str)
            transactions = transactions.filter(borrowed_at__date__gte=from_date)

        if to_date_str:
            to_date = parse_date(to_date_str)
            transactions = transactions.filter(borrowed_at__date__lte=to_date)

        if return_status != 'all':
            transactions = transactions.filter(status=(return_status == 'returned'))

        data = []
        for transaction in transactions:
            equipment_names = ', '.join([equipment.name for equipment in transaction.equipment.all()])
            borrowed_at = transaction.borrowed_at.strftime('%Y-%m-%d %H:%M:%S')
            returned_at = transaction.returned_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.returned_at else 'Not Returned'
            data.append({
                'student__name': transaction.student.name,
                'student__regno': transaction.student.regno,
                'equipment__name': equipment_names,
                'borrowed_at': borrowed_at,
                'returned_at': returned_at,
                'status': transaction.status,
            })

        return JsonResponse(data, safe=False)

@user_passes_test_custom(is_admin, 'dashboard-index')
def Admin_History(request):
    users = User.objects.filter(is_staff=False, is_superuser=False)
    # table data
    transactions_list = Transaction.objects.all().order_by('-borrowed_at')
    no_of_items = 15
    paginator = Paginator(transactions_list, no_of_items)
    page = request.GET.get('page')
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)

    context = {
        'items': items,
        'users': users
    }
    return render(request, 'UApp/Admin/aHistory.html', context)

@login_required
def admin_history_filter(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        search_str = data.get('searchText', '')
        from_date_str = data.get('fromDate', '')
        to_date_str = data.get('toDate', '')
        lab_filter = data.get('lab', 'all')

        transactions = Transaction.objects.all()

        if search_str:
            transactions = transactions.filter(
                Q(student__name__icontains=search_str) |
                Q(student__regno__icontains=search_str) |
                Q(equipment__name__icontains=search_str) |
                Q(handled_by__username__icontains=search_str)
            ).distinct()

        if from_date_str:
            from_date = parse_date(from_date_str)
            transactions = transactions.filter(borrowed_at__date__gte=from_date)

        if to_date_str:
            to_date = parse_date(to_date_str)
            transactions = transactions.filter(borrowed_at__date__lte=to_date)

        if lab_filter != 'all':
            transactions = transactions.filter(handled_by__username=lab_filter)

        data = []
        for transaction in transactions:
            equipment_names = ', '.join([equipment.name for equipment in transaction.equipment.all()])
            borrowed_at = transaction.borrowed_at.strftime('%Y-%m-%d %H:%M:%S')
            returned_at = transaction.returned_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.returned_at else 'Not Returned'
            data.append({
                'handled_by': transaction.handled_by.username if transaction.handled_by else 'Unknown',
                'student__name': transaction.student.name if transaction.student else 'Unknown',
                'student__regno': transaction.student.regno if transaction.student else 'Unknown',
                'equipment__name': equipment_names,
                'borrowed_at': borrowed_at,
                'returned_at': returned_at,
                'status': transaction.status,
            })

        return JsonResponse(data, safe=False)


#
# borrow & return
@user_passes_test_custom(is_user, 'dashboard-index')
def Borrow_Equipment(request):
    if request.method == 'POST':
        student_rfid = request.POST.get('rfidno')
        selected_equipments = request.POST.getlist('equipment[]')
        student = Student.objects.filter(rfidno=student_rfid).first()

        if student:
            try:
                with db_transaction.atomic():
                    equipment_objects = []
                    for equipment_name in selected_equipments:
                        equipment = Equipment.objects.filter(name=equipment_name).first()
                        if not equipment:
                            raise ValueError(f"Equipment {equipment_name} not found.")
                        equipment_objects.append(equipment)
                        equipment.available_count -= 1
                        equipment.save()

                    # Check for an existing transaction with status=False
                    existing_transaction = Transaction.objects.filter(student=student, status=False, handled_by=request.user).first()

                    if existing_transaction:
                        # Update the existing transaction
                        existing_transaction.equipment.add(*equipment_objects)
                        existing_transaction.borrowed_at = timezone.localtime()
                        existing_transaction.save()
                        messages.success(request, 'Equipment added to existing transaction successfully.')
                    else:
                        # Create a new transaction
                        transaction_record = Transaction.objects.create(
                            student=student,
                            borrowed_at=timezone.localtime(),
                            handled_by=request.user
                        )
                        transaction_record.equipment.set(equipment_objects)
                        transaction_record.save()
                        messages.success(request, 'New equipment borrowed successfully.')

            except ValueError as e:
                messages.error(request, f'An error occurred: {e}')
        else:
            messages.error(request, 'Student not found.')

        return redirect('dashboard-index')

    else:  # This is for handling GET requests
        current_datetime = timezone.localtime().strftime('%Y-%m-%dT%H:%M')
        context = {
            'current_datetime': current_datetime
        }
        return render(request, 'UApp/Records/add.html', context)

@user_passes_test_custom(is_user, 'dashboard-index')
def Return_Equipment(request):
    if request.method == 'POST':
        rfidno = request.POST.get('rfidno')
        if not rfidno:
            messages.error(request, "No RFID number provided.")
            return redirect('dashboard-index')

        try:
            student = Student.objects.get(rfidno=rfidno)
            transactions = Transaction.objects.filter(student=student, status=False)
            success_count = 0
            error_count = 0

            for transaction in transactions:
                try:
                    transaction.status = True 
                    transaction.returned_at = timezone.now() 
                    transaction.save()

                    for equipment in transaction.equipment.all():
                        equipment.available_count += 1
                        equipment.save()

                    success_count += 1
                except Exception as e:
                    error_count += 1
                    messages.error(request, f"Error returning item {transaction.equipment.all()}: {str(e)}")

            if success_count > 0:
                messages.success(request, f"{success_count} items returned successfully")
            if error_count > 0:
                messages.error(request, f"{error_count} items could not be returned")

        except Student.DoesNotExist:
            messages.error(request, "Student not found")

        return redirect('dashboard-index')

    else:
        current_datetime = timezone.localtime().strftime('%Y-%m-%dT%H:%M')
        context = {
            'current_datetime': current_datetime
        }
        return render(request, 'UApp/Records/return.html', context)

@login_required
def get_student_details(request):
    rfidno = request.GET.get('rfidno', None)
    if rfidno:
        try:
            student = Student.objects.get(rfidno=rfidno)
            transactions = Transaction.objects.filter(student=student, status=False, handled_by=request.user)
            borrowed_items = list(transactions.values('id', 'equipment__name', 'borrowed_at'))

            # Get the names of the equipment already borrowed and not returned
            borrowed_equipment_ids = transactions.values_list('equipment', flat=True)
            borrowed_equipment_names = Equipment.objects.filter(id__in=borrowed_equipment_ids).values_list('name', flat=True)

            # Get the available equipment that is not already borrowed by the student
            available_equipment = Equipment.objects.filter(lab=request.user, available_count__gt=0).exclude(id__in=borrowed_equipment_ids).values_list('name', flat=True)

            student_data = {
                'name': student.name,
                'regno': student.regno,
                'image_url': student.image.url,
                'borrowed_items': borrowed_items,
                'available_equipment': list(available_equipment)
            }
            return JsonResponse({'success': True, 'student': student_data})
        except Student.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Student not found'})
    return JsonResponse({'success': False, 'error': 'No RFID number provided'})


# 
# Equipments
@user_passes_test_custom(is_user, 'dashboard-index')
def EquipmentList(request):
    equipments_list = Equipment.objects.filter(lab=request.user)
    no_of_items = 10
    paginator = Paginator(equipments_list, no_of_items)
    page = request.GET.get('page')

    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)

    context = {
        'items': items
    }
    return render(request, 'UApp/Equipment/equipments.html', context)

@user_passes_test_custom(is_user, 'dashboard-index')
def Add_Equipment(request):
    if request.method == 'POST':
        form = AddEquipmentForm(request.POST)
        if form.is_valid():
            equipment = form.save(commit=False)
            equipment.lab = request.user
            equipment.available_count = equipment.count
            messages.success(request, 'Equipment added successfully.')
            equipment.save()
            return redirect('equipments-list')
    else:
        form = AddEquipmentForm()
    return render(request, 'UApp/Equipment/add_equipment.html', {'form': form})

@user_passes_test_custom(is_user, 'dashboard-index')
def Edit_Equipment(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    original_count = equipment.count

    if request.method == 'POST':
        form = EquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            equipment = form.save(commit=False)
            new_count = equipment.count

            if new_count != original_count:
                difference = new_count - original_count
                equipment.available_count = max(equipment.available_count + difference, 0)

            equipment.save()
            messages.success(request, 'Equipment edited successfully.')
            return redirect('equipments-list')
    else:
        form = EquipmentForm(instance=equipment)
    
    return render(request, 'UApp/Equipment/edit_equipment.html', {'form': form})

@user_passes_test_custom(is_user, 'dashboard-index')
def Delete_Equipment(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    if request.method == 'POST':
        equipment.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Handle AJAX request
            return JsonResponse({'status': 'success'}, status=200)
        else:
            # Handle traditional POST request
            messages.success(request, 'Equipment deleted successfully.')
            return redirect('equipments-list')
    return redirect('equipments-list')

@login_required
def Search_Equipment(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')
        equipment = Equipment.objects.filter(count__istartswith=search_str, lab=request.user) | Equipment.objects.filter(
            name__icontains=search_str, lab=request.user) | Equipment.objects.filter(category__icontains=search_str, lab=request.user)
        data = equipment.values()

        return JsonResponse(list(data), safe=False)


# 
# Students
@user_passes_test_custom(is_admin, 'dashboard-index')
def StudentList(request):
    students_list = Student.objects.all()
    no_of_items = 10
    paginator = Paginator(students_list, no_of_items)
    page = request.GET.get('page')

    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)

    context = {
        'items': items
    }
    return render(request, 'UApp/Student/students.html', context)
    
@user_passes_test_custom(is_admin, 'dashboard-index')
def Add_Student(request):
    if request.method == 'POST':
        student = Student(
            rfidno=request.POST.get('rfidno'),
            regno=request.POST.get('regno'),
            name=request.POST.get('studentName'),
            email=request.POST.get('studentemail'),
            phone=request.POST.get('studentphoneno'),
            department=request.POST.get('department'),
            course=request.POST.get('course'),
            year=request.POST.get('studentyear'),
            image=request.FILES.get(
                'studentphoto') if 'studentphoto' in request.FILES else 'avatar.png'
        )
        student.save()
        messages.success(request, 'Student added successfully!')
        return redirect('students-list')
    return render(request, 'UApp/Student/add_student.html')

@user_passes_test_custom(is_admin, 'dashboard-index')
def Upload_Students(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        df = pd.read_excel(file)
        # pip install odfpy
        # pip install pyxlsb
        # pip install xlrd
        # pip install openpyxl


        uploaded_count = 0
        failed_count = 0

        for index, row in df.iterrows():
            try:
                Student.objects.create(
                    rfidno=row['rfidno'],
                    regno=row['regno'],
                    name=row['name'],
                    email=row['email'],
                    phone=row['phone'],
                    department=row['department'],
                    course=row['course'],
                    year=row['year']
                )
                uploaded_count += 1
            except Exception as e:
                failed_count += 1

        if uploaded_count > 0:
            messages.success(request, f"{uploaded_count} records uploaded successfully.")
        if failed_count > 0:
            messages.error(request, f"{failed_count} records failed to upload.")

        return HttpResponseRedirect('/students')

    return render(request, 'UApp/Student/upload_student.html')

@user_passes_test_custom(is_admin, 'dashboard-index')
def Edit_Student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.rfidno = request.POST.get('rfidno')
        student.regno = request.POST.get('regno')
        student.name = request.POST.get('studentName')
        student.email = request.POST.get('studentemail')
        student.phone = request.POST.get('studentphoneno')
        student.department = request.POST.get('department')
        student.course = request.POST.get('course')
        student.year = request.POST.get('studentyear')
        student.image = request.FILES.get(
            'studentphoto') if 'studentphoto' in request.FILES else student.image
        student.save()
        messages.success(request, 'Student edited successfully!')
        return redirect('students-list')
    return render(request, 'UApp/Student/edit_student.html', {'student': student})

@user_passes_test_custom(is_admin, 'dashboard-index')
def Delete_Student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Handle AJAX request
            return JsonResponse({'status': 'success'}, status=200)
        messages.success(request, 'Student deleted successfully!')
        return redirect('students-list')
    return redirect('students-list')

@csrf_exempt
def Search_Student(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText', '')
        students = Student.objects.filter(name__icontains=search_str) | \
                   Student.objects.filter(regno__icontains=search_str) | \
                   Student.objects.filter(department__icontains=search_str) | \
                   Student.objects.filter(course__icontains=search_str) | \
                   Student.objects.filter(year__istartswith=search_str)
        data = list(students.values())
        return JsonResponse(data, safe=False)


# 
# Users or Lab
@user_passes_test_custom(is_admin, 'dashboard-index')
def UserList(request):
    users = User.objects.filter(is_staff=False, is_superuser=False)
    return render(request, 'UApp/User/users.html', {'users': users})

@user_passes_test_custom(is_admin, 'dashboard-index')
def create_User(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'New Lab created successfully.')
            return redirect('users-list')
    else:
        form = UserCreationForm()
    return render(request, 'UApp/User/add_user.html', {'form': form})

@user_passes_test_custom(is_admin, 'dashboard-index')
def Edit_User(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'Lab updated successfully.')
            return redirect('users-list') 
    else:
        form = UserEditForm(instance=user)
    return render(request, 'UApp/User/edit_user.html', {'form': form})

@user_passes_test_custom(is_admin, 'dashboard-index')
def View_User(request, pk):
    lab = get_object_or_404(User, pk=pk)
    equipment_count = Equipment.objects.filter(lab=lab).count()
    total_equipment_count = Equipment.objects.filter(lab=lab).aggregate(Sum('count'))
    total_available_equipment_count = Equipment.objects.filter(lab=lab).aggregate(Sum('available_count'))
    context = {
        'lab': lab,
        'equipment_count': equipment_count,
        'total_equipment_count': total_equipment_count['count__sum'] or 0,
        'total_available_equipment_count': total_available_equipment_count['available_count__sum'] or 0
    }
    return render(request, 'UApp/User/view_user.html', context)

@user_passes_test_custom(is_admin, 'dashboard-index')
def Delete_User(request, pk):
    user_to_delete = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        password = request.POST.get('admin_password')
        admin = authenticate(username=request.user.username, password=password)
        if admin:
            user_to_delete.delete()
            messages.success(request, 'Lab deleted successfully.')
            return redirect('users-list')
        else:
            messages.error(request, 'Incorrect password. Lab was not deleted.')
            return redirect('users-list')
    return render(request, 'UApp/User/delete_user.html', {'user': user_to_delete})

