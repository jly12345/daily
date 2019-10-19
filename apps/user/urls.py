 
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from apps.user import views
app_name = 'daily'

urlpatterns = [
    path('register', views.register),
]
