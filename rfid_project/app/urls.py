from django.urls import path
from . import views

urlpatterns = [
    path('',views.index, name='index'),
    path('add-equipment',views.add_equiments,name='addequipment'),
    path('return-equipment',views.return_equipments,name='returnequipment')
]
