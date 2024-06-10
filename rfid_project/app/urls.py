from django.urls import path
from . import views


urlpatterns = [
    path('',views.index, name='index'),
    path('add-equipment',views.add_equiments,name='addequipment'),
    path('return-equipment',views.return_equipments,name='returnequipment'),
    path('login', views.login_page, name='login'),
    path('logout', views.logout_page, name='logout'),
    path('register', views.register_page, name='register'),
]
