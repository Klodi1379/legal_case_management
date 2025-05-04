# cases/urls.py
from django.urls import path
from . import views
from . import views_conflict

app_name = 'cases'

urlpatterns = [
    # Case management
    path('', views.case_list, name='case_list'),
    path('<int:case_id>/', views.case_detail, name='case_detail'),
    path('create/', views.case_create, name='case_create'),
    path('<int:case_id>/update/', views.case_update, name='case_update'),

    # Conflict checks
    path('conflicts/', views_conflict.conflict_check_list, name='conflict_check_list'),
    path('conflicts/<int:check_id>/', views_conflict.conflict_check_detail, name='conflict_check_detail'),
    path('<int:case_id>/conflicts/', views_conflict.conflict_check_list, name='case_conflict_check_list'),
    path('<int:case_id>/conflicts/create/', views_conflict.conflict_check_create, name='conflict_check_create'),
    path('conflicts/<int:check_id>/resolve/', views_conflict.conflict_check_resolve, name='conflict_check_resolve'),
]