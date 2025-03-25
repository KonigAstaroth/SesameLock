from django.contrib import admin
from django.urls import path
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.signup, name="signup"),
    path('login/', views.login, name="login"),
    path('estadisticas/', views.estadisticas, name="estadisticas"),
    path('success/', views.add, name="add"),
    path('main/', views.inicio, name = 'inicio'),
    path('logout/', views.logout, name = "logout"),
    path('aboutsesame/', views.aboutSesame, name = "aboutSesame"),
    path('registerDevice/', views.regDev, name="regDev"),
    path('addGuests/', views.regInv, name="regInv"),
    path('signup/', views.signup, name="signup"),

    path('api/accesos-data/', views.api_accesos_data, name='api_accesos_data'),
    path('api/dia-mas-accesos/', views.api_dia_mas_accesos, name='api_dia_mas_accesos'),
]
