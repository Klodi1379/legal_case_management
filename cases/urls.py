# cases/urls.py
from django.urls import path
from . import views

app_name = 'cases'

urlpatterns = [
    path('', views.case_list, name='case_list'),
    path('<int:case_id>/', views.case_detail, name='case_detail'),
    path('create/', views.case_create, name='case_create'),
    path('<int:case_id>/update/', views.case_update, name='case_update'),
]