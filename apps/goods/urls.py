 
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from apps.goods import views
app_name = 'daily'
urlpatterns = [
    path('',views.index,name='index')
]
