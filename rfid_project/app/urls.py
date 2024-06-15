from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('', views.login_page, name='login'),
    path('Dashboard',views.index, name='index'),
    path('borrow-equipment',views.borrow_equiments,name='borrowequipment'),
    path('return-equipment',views.return_equipments,name='returnequipment'),
    path('logout', views.logout_page, name='logout'),
    path('register', views.register_page, name='register'),
    path('add-equipment',views.add_equiments,name='addequipment'),
    path('history',views.history,name='history'),
    path('equipment',views.equipments,name='equipments'),
    path('edit-equipment/<int:id>',views.edit_equipment,name='editequipment'),
    path('delete-equipment/<int:id>',views.delete_equipment,name='deleteequipment'),
    path('search-equipment', views.search_equipment, name='searchequipment'),
]
