from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='dashboard-index'),
    path('admin-dashboard/<int:pk>/', views.admin_dashboard, name='admin-dashboard'),

    # path('register/', views.register, name='Register'),
    path('login/', auth_views.LoginView.as_view(template_name='UApp/Auth/login.html'), name='Login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='Login'), name='Logout'),

    path('about/', views.about, name='about'),
    path('settings/', views.settings, name='settings'),

    path('history/', views.History, name='history'),
    path('search-history/', views.history_filter, name='search-history'),

    path('admin-history/', views.Admin_History, name='admin-history'),
    path('admin-search-history/', views.admin_history_filter, name='admin-search-history'),
    path('export-history/', views.export_history, name='export-history'),

    path('create/', views.Borrow_Equipment, name='borrow-equipment'),
    path('return/', views.Return_Equipment, name='return-equipment'),
    path('get_student_details/', views.get_student_details, name='get-student-details'),

    path('equipments/', views.EquipmentList, name='equipments-list'),
    path('equipments/add/', views.Add_Equipment, name='add-equipment'),
    path('equipment/edit/<int:pk>/', views.Edit_Equipment, name='edit-equipment'),
    path('equipment/delete/<int:pk>/', views.Delete_Equipment, name='delete-equipment'),
    path('search-equipment', views.Search_Equipment, name='search-equipment'),

    path('equipments/medical-kit/add/', views.Add_MedicalKit, name='add-medicalKit'),
    path('equipments/medical-kit/edit/<int:kit_id>/', views.Edit_MedicalKit, name='edit-medicalkit'),
    path('equipments/medical-kit/delete/<int:pk>/', views.Delete_MedicalKit, name='delete-medicalkit'),

    path('students/', views.StudentList, name='students-list'),
    path('students/add/', views.Add_Student, name='add-student'),
    path('students/edit/<int:pk>/', views.Edit_Student, name='edit-student'),
    path('students/delete/<int:pk>/', views.Delete_Student, name='delete-student'),
    path('search-student', views.Search_Student, name='search-student'),
    path('students/upload/',views.Upload_Students, name='upload-student'),

    path('users/', views.UserList, name='users-list'),
    path('users/add/', views.create_User, name='add-user'),
    path('users/view/<int:pk>/', views.View_User, name='view-user'),
    path('users/edit/<int:pk>/', views.Edit_User, name='edit-user'),
    path('users/delete/<int:pk>/', views.Delete_User, name='delete-user'),

]
