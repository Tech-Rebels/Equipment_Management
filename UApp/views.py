import json
import pandas as pd
import openpyxl
import logging
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Count, Sum, Q, F, Max, BooleanField, Case, When, Value, CharField
from django.db.models.functions import Concat, Coalesce
from django.db import transaction as db_transaction
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .forms import CreateUserForm, UserEditForm, AddEquipmentForm, EquipmentForm, AddMedicalKitForm, AddTreatmentForm, EditTreatmentForm
from .models import Equipment, Student, Transaction, MedicalKit, Treatment

# Set up logging
logger = logging.getLogger(__name__)

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
        # card data
        today = timezone.localdate()
        total_equipment_count = Equipment.objects.filter(lab=request.user).aggregate(Sum('count'))
        borrowed_count_data = Transaction.objects.filter(handled_by=request.user, borrowed_at__date=today).annotate(equipment_count=Count('equipment')).aggregate(total=Sum('equipment_count'))
        not_returned_count_data = Transaction.objects.filter(handled_by=request.user, status=False, borrowed_at__date=today).annotate(equipment_count=Count('equipment')).aggregate(total=Sum('equipment_count'))
        borrowed_count = borrowed_count_data['total'] or 0
        not_returned_count = not_returned_count_data['total'] or 0
        returned_count = borrowed_count - not_returned_count
        pending_count_data = Transaction.objects.filter(handled_by=request.user, status=False).annotate(equipment_count=Count('equipment')).aggregate(total=Sum('equipment_count'))
        pending_count = pending_count_data['total'] or 0
        transactions_count = Transaction.objects.filter(handled_by=request.user, borrowed_at__date=today).count()

        # status filter logic
        status_filter = request.GET.get('status', 'all')  # 'all' by default if no status filter is selected
        if status_filter == 'returned':
            transactions_list = Transaction.objects.filter(handled_by=request.user, status=True, borrowed_at__date=today)
        elif status_filter == 'not_returned':
            transactions_list = Transaction.objects.filter(handled_by=request.user, status=False, borrowed_at__date=today)
        else:
            transactions_list = Transaction.objects.filter(handled_by=request.user, borrowed_at__date=today)

        transactions_list = transactions_list.order_by('status', 'borrowed_at')

        # pagination
        no_of_items = 13
        paginator = Paginator(transactions_list, no_of_items)
        page = request.GET.get('page')
        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            items = paginator.page(1)
        except EmptyPage:
            items = paginator.page(paginator.num_pages)

        # past dates not returned
        past_not_returned_items = Transaction.objects.filter(
            handled_by=request.user, status=False, borrowed_at__date__lt=today).order_by('borrowed_at')

        context = {
            'items': items,
            'total_equipment_count': total_equipment_count['count__sum'] or 0,
            'borrowed_count': borrowed_count,
            'not_returned_count': not_returned_count,
            'returned_count': returned_count,
            'pending_count': pending_count,
            'status_filter': status_filter,
            'transactions_count': transactions_count,
            'past_not_returned_items': past_not_returned_items
        }
        return render(request, 'UApp/index.html', context)
    elif request.user.is_staff:
        users = User.objects.filter(is_staff=False, is_superuser=False)
        context = {
            'users': users
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
    pending_count_data = Transaction.objects.filter(handled_by=lab, status=False).annotate(equipment_count=Count('equipment')).aggregate(total=Sum('equipment_count'))
    pending_count = pending_count_data['total'] or 0
    transactions_count = Transaction.objects.filter(handled_by=lab, borrowed_at__date=today).count()

    # table data - without status
    # transactions_list = Transaction.objects.filter(handled_by=lab, borrowed_at__date=today).order_by('status','-borrowed_at') # , borrowed_at__date=today
    
    # status filter logic
    status_filter = request.GET.get('status', 'all')  # 'all' by default if no status filter is selected
    if status_filter == 'returned':
        transactions_list = Transaction.objects.filter(handled_by=lab, status=True, borrowed_at__date=today)
    elif status_filter == 'not_returned':
        transactions_list = Transaction.objects.filter(handled_by=lab, status=False, borrowed_at__date=today)
    else:
        transactions_list = Transaction.objects.filter(handled_by=lab, borrowed_at__date=today)

    transactions_list = transactions_list.order_by('status', 'borrowed_at')


    # pagination
    no_of_items = 13
    paginator = Paginator(transactions_list, no_of_items)
    page = request.GET.get('page')
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)

    # past dates not returned
    past_not_returned_items = Transaction.objects.filter(
        handled_by=lab, status=False, borrowed_at__date__lt=today).order_by('borrowed_at')

    context = {
        'lab' : lab,
        'items': items,
        'total_equipment_count': total_equipment_count['count__sum'] or 0,
        'borrowed_count': borrowed_count,
        'not_returned_count': not_returned_count,
        'status_filter': status_filter,
        'returned_count': returned_count,
        'pending_count': pending_count,
        'transactions_count': transactions_count,
        'past_not_returned_items': past_not_returned_items
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
                Q(studentName__icontains=search_str) |
                Q(studentRegno__icontains=search_str) |
                Q(equipmentName__icontains=search_str) |
                Q(treatmentName__icontains=search_str)
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
            # equipment_names = ', '.join([equipment.name for equipment in transaction.equipment.all()])
            borrowed_at = transaction.borrowed_at.strftime('%Y-%m-%d %H:%M:%S')
            returned_at = transaction.returned_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.returned_at else 'Not Returned'
            data.append({
                'student__name': transaction.studentName,
                'student__regno': transaction.studentRegno,
                'equipment__name': transaction.equipmentName,
                'treatment__name': transaction.treatmentName,
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
        return_status = data.get('returnStatus', 'all')

        transactions = Transaction.objects.all()

        if search_str:
            transactions = transactions.filter(
                Q(studentName__icontains=search_str) |
                Q(studentRegno__icontains=search_str) |
                Q(equipmentName__icontains=search_str) |
                Q(treatmentName__icontains=search_str) |
                Q(labName__icontains=search_str)
            ).distinct()

        if from_date_str:
            from_date = parse_date(from_date_str)
            transactions = transactions.filter(borrowed_at__date__gte=from_date)

        if to_date_str:
            to_date = parse_date(to_date_str)
            transactions = transactions.filter(borrowed_at__date__lte=to_date)

        if lab_filter != 'all':
            transactions = transactions.filter(handled_by__username=lab_filter)
        
        if return_status != 'all':
            transactions = transactions.filter(status=(return_status == 'returned'))

        data = []
        for transaction in transactions:
            borrowed_at = transaction.borrowed_at.strftime('%Y-%m-%d %H:%M:%S')
            returned_at = transaction.returned_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.returned_at else 'Not Returned'
            data.append({
                'handled_by': transaction.labName if transaction.labName else 'Unknown',
                'student__name': transaction.studentName if transaction.studentName else 'Unknown',
                'student__regno': transaction.studentRegno if transaction.studentRegno else 'Unknown',
                'equipment__name': transaction.equipmentName,
                'treatment__name': transaction.treatmentName,
                'borrowed_at': borrowed_at,
                'returned_at': returned_at,
                'status': transaction.status,
            })

        return JsonResponse(data, safe=False)

@login_required
def export_history(request):
    from_date = request.GET.get('fromDate')
    to_date = request.GET.get('toDate')
    search_str = request.GET.get('search', '')
    lab = request.GET.get('dropdownSelect', 'all')
    return_status = request.GET.get('returndropdownSelect', 'all')

    # print(from_date, to_date, search_str, lab, return_status)

    # Filter transactions based on the provided filters
    transactions = Transaction.objects.all()

    if search_str:
            transactions = transactions.filter(
                Q(studentName__icontains=search_str) |
                Q(studentRegno__icontains=search_str) |
                Q(equipmentName__icontains=search_str) |
                Q(treatmentName__icontains=search_str) |
                Q(labName__icontains=search_str)
            ).distinct()

    if from_date:
        transactions = transactions.filter(borrowed_at__date__gte=from_date)
    if to_date:
        transactions = transactions.filter(borrowed_at__date__lte=to_date)
    # if lab != 'all':
    #     transactions = transactions.filter(handled_by__username=lab)
    if request.user.is_staff:
        if lab != 'all':
            transactions = transactions.filter(handled_by__username=lab)
    else:
        transactions = transactions.filter(handled_by__username=request.user.username)
    

    if return_status == 'returned':
        transactions = transactions.filter(status=True)
    elif return_status == 'notreturned':
        transactions = transactions.filter(status=False)

    # Create a workbook and sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Transaction History'


    headers = ['Lab', 'Name', 'Reg.No.', 'Instrument','Treated for', 'Borrow Time', 'Return Time', 'Status']
    ws.append(headers)

    # Write the data
    for transaction in transactions:
        ws.append([
            transaction.labName if transaction.labName else '',
            transaction.studentName if transaction.studentName else '',  # Handle None case
            transaction.studentRegno if transaction.studentRegno else '',  # Handle None case
            transaction.equipmentName if transaction.equipmentName else '',  # Handle empty equipment names
            transaction.treatmentName if transaction.treatmentName else '',  # Handle empty equipment names
            transaction.borrowed_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.borrowed_at else '',
            transaction.returned_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.returned_at else 'Not Returned',
            'Returned' if transaction.status else 'Not Returned'
        ])

    # Prepare the response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename=DIMS_transaction_history_{timezone.now().strftime("%Y-%m-%d_%H-%M-%S")}.xlsx'
    wb.save(response)

    return response


#
# borrow & return
@user_passes_test_custom(is_user, 'dashboard-index')
def Borrow_Equipment(request):
    if request.method == 'POST':
        student_rfid = request.POST.get('rfidno')
        selected_items = request.POST.getlist('equipment[]')  # Get both equipment and medkits
        selected_treatment = request.POST.getlist('treatment[]')  # Get both equipment and medkits
        student = Student.objects.filter(rfidno=student_rfid).first()

        if student:
            try:
                with db_transaction.atomic():
                    equipment_objects = []
                    treatment_objects = []
                    for item_name in selected_items:
                        # Check if the item is a medkit or equipment
                        medkit = MedicalKit.objects.filter(kitName=item_name).first()
                        if medkit:
                            # Handle medkit borrowing
                            for equipment in medkit.equipment.all():
                                if equipment.available_count <= 0:
                                    raise ValueError(f"Equipment {equipment.name} in medkit {medkit.name} is unavailable.")
                                equipment.available_count -= 1
                                equipment.save()
                                equipment_objects.append(equipment)
                        else:
                            # Handle individual equipment borrowing
                            equipment = Equipment.objects.filter(name=item_name).first()
                            if not equipment:
                                raise ValueError(f"Equipment {item_name} not found.")
                            if equipment.available_count <= 0:
                                raise ValueError(f"Equipment {item_name} is unavailable.")
                            equipment.available_count -= 1
                            equipment.save()
                            equipment_objects.append(equipment)

                    for treatment_name in selected_treatment:
                        treatment = Treatment.objects.filter(treatment=treatment_name).first()
                        if treatment:
                            treatment_objects.append(treatment)
                        else:
                            raise ValueError(f"Treatment {treatment_name} not found.")

                    # Check for an existing transaction with status=False
                    existing_transaction = Transaction.objects.filter(student=student, status=False, handled_by=request.user).first()

                    if existing_transaction:
                        existing_transaction.equipment.add(*equipment_objects)
                        # existing_transaction.treatment.add(*treatment_objects)
                        existing_transaction.treatment.set(treatment_objects)
                        existing_transaction.borrowed_at = timezone.localtime()
                        existing_transaction.save()
                        messages.success(request, 'Equipment/Medkit added to existing transaction successfully.')
                    else:
                        transaction_record = Transaction.objects.create(
                            student=student,
                            borrowed_at=timezone.localtime(),
                            handled_by=request.user
                        )
                        transaction_record.equipment.set(equipment_objects)
                        transaction_record.treatment.set(treatment_objects)
                        transaction_record.save()
                        messages.success(request, 'New Equipment/Medkit borrowed successfully.')

            except ValueError as e:
                messages.error(request, f'An error occurred: {e}')
        else:
            messages.error(request, 'Student not found.')

        return redirect('dashboard-index')

    else:  # Handling GET requests
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
            transactions = Transaction.objects.filter(student=student, status=False, handled_by=request.user)
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

            other_lab_transactions = Transaction.objects.filter(student=student, status=False).exclude(handled_by=request.user).select_related('handled_by').prefetch_related('equipment')
            
            other_lab_borrowed_items = []
            other_lab_name = None
            
            if other_lab_transactions.exists():
                other_lab_name = other_lab_transactions.first().handled_by.get_full_name() or other_lab_transactions.first().handled_by.username
                
                other_lab_borrowed_items = list(other_lab_transactions.values(
                    'id', 
                    'equipment__name', 
                    'borrowed_at',
                    'handled_by__username',
                    'handled_by__first_name',
                    'handled_by__last_name'
                ))
                
                for item in other_lab_borrowed_items:
                    lab_name = f"{item['handled_by__first_name']} {item['handled_by__last_name']}".strip()
                    if not lab_name:
                        lab_name = item['handled_by__username']
                    item['lab_name'] = lab_name

            borrowed_equipment_ids = transactions.values_list('equipment', flat=True)
            borrowed_treatment_ids = transactions.values_list('treatment', flat=True)
            previously_selected_treatments = transactions.values_list('treatment__treatment', flat=True)

            available_equipment = Equipment.objects.filter(lab=request.user, available_count__gt=0).exclude(id__in=borrowed_equipment_ids).order_by(Coalesce('order', Value(float('inf'))).asc()).values_list('name', flat=True)
            available_medkits = MedicalKit.objects.filter(lab=request.user).exclude(Q(equipment__available_count__lte=0) | Q(equipment__id__in=borrowed_equipment_ids)).order_by(Coalesce('order', Value(float('inf'))).asc()).values_list('kitName', flat=True)  
            treatment = Treatment.objects.filter(lab=request.user).order_by(Coalesce('order', Value(float('inf'))).asc()).values_list('treatment', flat=True)  

            student_data = {
                'name': student.name,
                'regno': student.regno,
                'image_url': student.image.url,
                'borrowed_items': borrowed_items,
                'other_lab_borrowed_items': other_lab_borrowed_items,
                'other_lab_name': other_lab_name,
                'available_equipment': list(available_medkits) + list(available_equipment),
                'borrowed_treatment_ids': list(previously_selected_treatments),
                'treatment': list(treatment)
            }
            return JsonResponse({'success': True, 'student': student_data})
        except Student.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Student not found'})
    return JsonResponse({'success': False, 'error': 'No RFID number provided'})


# 
# Equipments
@user_passes_test_custom(is_user, 'dashboard-index')
def EquipmentList(request):
    equipments_list = Equipment.objects.filter(lab=request.user).order_by(Coalesce(F('order'), Value('99999')),'order')
    medKit_list = MedicalKit.objects.filter(lab=request.user).order_by(Coalesce(F('order'), Value('99999')),'order')
    # no_of_items = 10
    # paginator = Paginator(equipments_list, no_of_items)
    # page = request.GET.get('page')

    # try:
    #     items = paginator.page(page)
    # except PageNotAnInteger:
    #     items = paginator.page(1)
    # except EmptyPage:
    #     items = paginator.page(paginator.num_pages)

    context = {
        'items': equipments_list,
        'medKit': medKit_list

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

            # Case-insensitive duplicate check
            if Equipment.objects.filter(lab=request.user, name__iexact=equipment.name).exists():
                messages.error(request, 'An instrument with this name already exists in your lab (case-insensitive).')
                return render(request, 'UApp/Equipment/add_equipment.html', {'form': form})

            try:
                # Normalize name before saving (e.g., capitalize)
                equipment.name = equipment.name.strip().capitalize()
                equipment.save()
                messages.success(request, 'Instrument added successfully.')
                return redirect('equipments-list')
            except Exception as e:
                messages.error(request, 'An error occurred while adding the equipment.')
                return render(request, 'UApp/Equipment/add_equipment.html', {'form': form})
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

            # Case-insensitive duplicate check
            if (
                Equipment.objects.filter(lab=equipment.lab, name__iexact=equipment.name)
                .exclude(pk=equipment.pk)
                .exists()
            ):
                messages.error(request, f'An instrument with the name "{equipment.name}" already exists in your lab (case-insensitive).')
                return render(request, 'UApp/Equipment/edit_equipment.html', {'form': form})

            if new_count != original_count:
                difference = new_count - original_count
                equipment.available_count = max(equipment.available_count + difference, 0)

            # Normalize name before saving (e.g., capitalize)
            equipment.name = equipment.name.strip().capitalize()
            equipment.save()
            messages.success(request, 'Instrument edited successfully.')
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
            messages.success(request, 'Instrument deleted successfully.')
            return redirect('equipments-list')
    return redirect('equipments-list')

@login_required
def Search_Equipment(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')
        equipment = Equipment.objects.filter(count__istartswith=search_str, lab=request.user) | Equipment.objects.filter(
            name__icontains=search_str, lab=request.user) | Equipment.objects.filter(category__icontains=search_str, lab=request.user)
        kits = MedicalKit.objects.filter(kitName__icontains=search_str, lab=request.user) 
        
        equipment_data = list(equipment.values())
        kit_data = []
        for kit in kits:
            kit_data.append({
                'id': kit.id,
                'kitName': kit.kitName,
                'lab': kit.lab.username if kit.lab else None,
                'equipments': ', '.join(equipment.name for equipment in kit.equipment.all())
            })

        data = {
            'equipment': equipment_data,
            'kit': kit_data
        }

        return JsonResponse(data, safe=False)

@login_required
def suggest_equipment(request):
    query = request.GET.get('query', '')
    suggestions = Equipment.objects.filter(name__icontains=query, lab=request.user).values('name', 'id')[:5]
    return JsonResponse(list(suggestions), safe=False)

# Medical Kit
@user_passes_test_custom(is_user, 'dashboard-index')
def Add_MedicalKit(request):
    if request.method == 'POST':
        kit_name = request.POST.get('medKitName')
        equipment_ids = request.POST.getlist('equipment[]')
        order = request.POST.get('order')

        if order == '':
            order = None

        try:
            medical_kit = MedicalKit.objects.create(
                kitName=kit_name,
                lab=request.user,
                order=order
            )

            if equipment_ids:
                equipment_objects = Equipment.objects.filter(id__in=equipment_ids)
                medical_kit.equipment.set(equipment_objects)

            messages.success(request, 'Instrument Kit added successfully.')
            return redirect('equipments-list')

        except Exception as e:
            messages.error(request, f"Error adding Instrument Kit: {str(e)}")

    else:
        items = Equipment.objects.filter(lab=request.user).order_by(Coalesce(F('order'), Value('99999')), 'order')
        context = {
            'items': items
        }

    return render(request, 'UApp/Equipment/MedKit/add_medKit.html', context)

@user_passes_test_custom(is_user, 'dashboard-index')
def Edit_MedicalKit(request, kit_id):
    medical_kit = get_object_or_404(MedicalKit, id=kit_id)

    if request.method == 'POST':
        kit_name = request.POST.get('medKitName')
        equipment_ids = request.POST.getlist('equipment[]')
        order = request.POST.get('order')

        try:
            if order == '':
                order = None

            medical_kit.kitName = kit_name
            medical_kit.order = order
            medical_kit.save()

            equipment_objects = Equipment.objects.filter(id__in=equipment_ids)
            medical_kit.equipment.set(equipment_objects)

            messages.success(request, 'Instrument kit updated successfully!')
            return redirect('equipments-list')

        except Exception as e:
            messages.error(request, f"Instrument Kit not updated: {str(e)}")

    else:
        items = Equipment.objects.filter(lab=request.user).order_by(Coalesce(F('order'), Value('99999')), 'order')
        selected_equipment_ids = medical_kit.equipment.values_list('id', flat=True)

        context = {
            'items': items,
            'medical_kit': medical_kit,
            'selected_equipment_ids': selected_equipment_ids
        }

    return render(request, 'UApp/Equipment/MedKit/edit_medKit.html', context)

@user_passes_test_custom(is_user, 'dashboard-index')
def Delete_MedicalKit(request, pk):
    try:
        medical_kit = get_object_or_404(MedicalKit, pk=pk)
        
        if request.method == 'POST':
            medical_kit.delete()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'}, status=200)
            else:
                messages.success(request, 'Instrument Kit deleted successfully.')
                return redirect('equipments-list')
                
        return JsonResponse({'status': 'failure', 'message': 'Invalid request method'}, status=400)
    
    except MedicalKit.DoesNotExist:
        return JsonResponse({'status': 'failure', 'message': 'Instrument Kit not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# 
# Treatment
@user_passes_test_custom(is_user, 'dashboard-index')
def TreatmentList(request):
    treatment_list = Treatment.objects.filter(lab=request.user).order_by(Coalesce(F('order'), Value('99999')),'order')
    # no_of_items = 10
    # paginator = Paginator(treatment_list, no_of_items)
    # page = request.GET.get('page')

    # try:
    #     items = paginator.page(page)
    # except PageNotAnInteger:
    #     items = paginator.page(1)
    # except EmptyPage:
    #     items = paginator.page(paginator.num_pages)

    context = {
        'items': treatment_list,
    }

    return render(request, 'UApp/Treatment/treatments.html', context)

@user_passes_test_custom(is_user, 'dashboard-index')
def Add_Treatment(request):
    if request.method == 'POST':
        form = AddTreatmentForm(request.POST)
        if form.is_valid():
            treat = form.save(commit=False)
            treat.lab = request.user

            # Check for duplicates within the same lab
            if Treatment.objects.filter(lab=request.user, treatment__iexact=treat.treatment).exists():
                messages.error(request, 'This treatment already exists in your lab.')
                return render(request, 'UApp/Treatment/add_treatment.html', {'form': form})
            
            treat.save()
            messages.success(request, 'Treatment added successfully.')
            return redirect('treatments-list')
    else:
        form = AddTreatmentForm()
    return render(request, 'UApp/Treatment/add_treatment.html', {'form': form})

@user_passes_test_custom(is_user, 'dashboard-index')
def Edit_Treatment(request, pk):
    treatment = get_object_or_404(Treatment, id=pk, lab=request.user)

    if request.method == 'POST':
        form = EditTreatmentForm(request.POST, instance=treatment)
        if form.is_valid():
            updated_treatment = form.save(commit=False)

            # Check for duplicates within the same lab (excluding the current treatment)
            if Treatment.objects.filter(lab=request.user, treatment__iexact=updated_treatment.treatment).exclude(id=treatment.id).exists():
                messages.error(request, 'This treatment already exists in your lab.')
                return render(request, 'UApp/Treatment/edit_treatment.html', {'form': form})

            updated_treatment.save()
            messages.success(request, 'Treatment edited successfully.')
            return redirect('treatments-list')
    else:
        form = EditTreatmentForm(instance=treatment)

    return render(request, 'UApp/Treatment/edit_treatment.html', {'form': form})

@user_passes_test_custom(is_user, 'dashboard-index')
def Delete_Treatment(request, pk):
    treat = get_object_or_404(Treatment, pk=pk)
    if request.method == 'POST':
        treat.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'}, status=200)
        else:
            messages.success(request, 'Treatment deleted successfully.')
            return redirect('treatments-list')
    return redirect('treatments-list')


# 
# order change
def Update_Order(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        ordered_ids = data.get('ordered_ids', [])
        item_type = data.get('type', '')  # Get the type of item (equipment, treatment, etc.)

        if item_type == 'equipment':
            model = Equipment
        elif item_type == 'treatment':
            model = Treatment
        elif item_type == 'medkit':
            model = MedicalKit
        else:
            return JsonResponse({'success': False, 'error': 'Invalid item type'}, status=400)

        for index, item_id in enumerate(ordered_ids):
            model.objects.filter(id=item_id).update(order=index)

        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


# 
# Students
@user_passes_test_custom(is_admin, 'dashboard-index')
def StudentList(request):
    students_list = Student.objects.all().order_by('id')
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
        rfidno = request.POST.get('rfidno', '')
        regno = request.POST.get('regno', '')
        name = request.POST.get('studentName', '')
        email = request.POST.get('studentemail', '')
        phone = request.POST.get('studentphoneno', '')
        dob = request.POST.get('dob', '')
        year = request.POST.get('studentyear', '')

        # Handle date format and conversion
        if dob:
            dob = parse_date(dob)
            if not dob:
                messages.error(request, 'Invalid date format. Ensure it is in YYYY-MM-DD format.')
                return redirect('add-student')

        image = request.FILES.get('studentphoto', 'avatar.png')

        try:
            student = Student(
                rfidno=rfidno,
                regno=regno,
                name=name,
                email=email,
                phone=phone,
                dob=dob if dob else None,  # Set to None if dob is empty
                year=year,
                image=image
            )
            student.save()
            messages.success(request, 'Student added successfully!')
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            messages.error(request, f'Validation error: {str(e)}')
        except Exception as e:
            logger.error(f"Error saving student: {e}")
            messages.error(request, f'Failed to add student: {str(e)}')
        
        return redirect('students-list')

    return render(request, 'UApp/Student/add_student.html')

@user_passes_test_custom(is_admin, 'dashboard-index')
def Upload_Students(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']

        try:
            df = pd.read_excel(file, dtype=str)
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            messages.error(request, 'Failed to read the file. Please ensure it is a valid Excel file.')
            return redirect('upload-student')

        df.columns = df.columns.str.strip().str.lower()

        required_columns = {'rfidno', 'regno', 'name'}
        missing_columns = required_columns - set(df.columns)

        if missing_columns:
            messages.error(request, f"Missing columns in the file: {', '.join(missing_columns)}")
            return redirect('upload-student')
        

        uploaded_count = 0
        failed_count = 0
        invalid_rows = []

        for index, row in df.iterrows():
            try:
                dob = row.get('dob', None)
                if pd.notna(dob):
                    try:
                        dob = pd.to_datetime(dob, dayfirst=True).date() 
                    except ValueError:
                        dob = None 
                email = row.get('email', None) if pd.notna(row.get('email', None)) else None
                phone = row.get('phone', None) if pd.notna(row.get('phone', None)) else None
                year = row.get('year', None) if pd.notna(row.get('year', None)) else None

                Student.objects.create(
                    rfidno=row.get('rfidno', None),
                    regno=row.get('regno', None),
                    name=row.get('name', None),
                    email=email,
                    phone=phone,
                    dob=dob,
                    year=year
                )
                uploaded_count += 1
            except Exception as e:
                logger.error(f"Error processing row {index + 1}: {str(e)}")
                failed_count += 1
                invalid_rows.append(index + 1) 

        if uploaded_count > 0:
            messages.success(request, f"{uploaded_count} records uploaded successfully.")
        if failed_count > 0:
            if invalid_rows:
                messages.error(request, f"{failed_count} records failed to upload. Rows with errors: {', '.join(map(str, invalid_rows))}.")
            else:
                messages.error(request, f"{failed_count} records failed to upload. Please check the file for errors.")
        if uploaded_count == 0 and failed_count > 0:
            messages.error(request, "No records were uploaded due to errors in the file.")

        return redirect('students-list')

    return render(request, 'UApp/Student/upload_student.html')

@user_passes_test_custom(is_admin, 'dashboard-index')
def Edit_Student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    # print('Date of Birth:', student.dob)
    if request.method == 'POST':
        student.rfidno = request.POST.get('rfidno')
        student.regno = request.POST.get('regno')
        student.name = request.POST.get('studentName')
        student.email = request.POST.get('studentemail')
        student.phone = request.POST.get('studentphoneno')
        # student.dob=request.POST.get('dob', None)
        dob = request.POST.get('dob', None)
        if dob:
            try:
                student.dob = pd.to_datetime(dob, format='%Y-%m-%d').date()  # Ensure format matches input
            except ValueError:
                student.dob = None
        else:
            student.dob = None
        # student.department = request.POST.get('department')
        # student.course = request.POST.get('course')
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
                   Student.objects.filter(email__icontains=search_str) | \
                   Student.objects.filter(year__icontains=search_str)
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

