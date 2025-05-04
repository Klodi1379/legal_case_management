# portal/urls.py
from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    # Client portal views
    path('', views.portal_home, name='home'),
    path('dashboard/', views.client_dashboard, name='dashboard'),
    path('cases/', views.client_cases, name='cases'),
    path('cases/<int:case_id>/', views.client_case_detail, name='case_detail'),
    path('documents/', views.client_documents, name='documents'),
    path('messages/', views.client_messages, name='messages'),
    path('messages/create/', views.create_message, name='create_message'),
    path('messages/<int:thread_id>/', views.message_thread, name='message_thread'),
    path('profile/', views.client_profile, name='profile'),
]
