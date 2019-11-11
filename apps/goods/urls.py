 
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from apps.goods.views import IndexView,DetailView,ListView
app_name = 'daily'
urlpatterns = [
    path('',IndexView.as_view(),name='index'),
    path('detail/<id>',DetailView.as_view(),name='detail'),
    path('list/<int:type_id>/<int:page>',ListView.as_view(),name='list')
]
