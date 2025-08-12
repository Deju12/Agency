from django.urls import path
from app import views

urlpatterns = [
    path('login', views.login_view),
    path('forgot-password', views.forgot_password_view),
    path('check-db', views.check_db_connection),
    #path("applicants/", views.list_applicants),
    #path("applicants/create/", views.create_applicant),
    path("applicants/<int:applicant_id>/", views.get_applicant),
    path("applicants/<int:applicant_id>/update", views.update_applicant),
    path("applicants/<int:applicant_id>/delete", views.delete_applicant),
    path('applicants', views.list_applicants_full, name='list_applicants_full'),
    path('applicants/create', views.create_applicant, name='create_applicant'),
]
