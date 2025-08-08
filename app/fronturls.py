from django.urls import path
from .views import check_db_connection, login_view, forgot_password_view
from app.frontView.views import dashboard, login, forgot_password
urlpatterns = [
    path('', login, name="login"),
    path('forgot-password', forgot_password, name="forgot_password"),
    path('dashboard', dashboard, name="dashboard"),
    
]
