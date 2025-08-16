from django.urls import path
from app import views

urlpatterns = [
    path('login', views.login_view),
    path('forgot-password', views.forgot_password_view),
    path('check-db', views.check_db_connection),
    
    # Users
    path("users", views.get_all_users, name="get_all_users"),
    path("users/create", views.create_user, name="create_user"),
    path("users/update/<str:user_id>", views.update_user, name="update_user"),
    path("users/delete/<str:user_id>", views.delete_user, name="delete_user"),
    
    # Applicants
    path('applicants', views.list_applicants_full, name='list_applicants_full'),
    path('applicants/create', views.create_applicant, name='create_applicant'),
    path("applicants/update/<str:applicant_id>", views.update_applicant),
    path("applicants/delete/<str:applicant_id>", views.delete_applicant),
]

