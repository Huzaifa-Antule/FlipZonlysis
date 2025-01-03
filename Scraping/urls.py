from django.urls import path
from .views import Home,AboutUs,Login,Logout,Register,Dashboard

urlpatterns = [
    path('',Home,name="home"),
    path('about',AboutUs,name="about"),
    path('register',Register,name="register"),
    path('login',Login,name="login"),
    path('logout',Logout,name="logout"),
    path('dashboard',Dashboard,name="dashboard"),
       
]